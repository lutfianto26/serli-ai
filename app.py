import streamlit as st
import sqlite3, json, os, uuid
from datetime import datetime

st.set_page_config(page_title='SERLI-AI', page_icon='🧠', layout='wide')
DB='serli_ai.db'

SYSTEM_PROMPT = '''Anda adalah SERLI-AI, asisten pembelajaran untuk siswa SMP yang membantu memahami konsep fungsi secara holistik melalui Self-Regulated Learning (SRL) Zimmerman: Forethought, Performance, dan Self-Reflection. Utamakan pemahaman daripada jawaban. Pertanyaan siswa menjadi penggerak pembelajaran. Gunakan bahasa Indonesia sederhana dan natural. Jangan menjadikan percakapan sebagai kuesioner SRL.

FORETHOUGHT: bantu goal setting, aktivasi pengetahuan awal, task analysis, strategic planning.
PERFORMANCE: gunakan micro-loop PLAN→ATTEMPT→MONITOR→HELP→REVISE→CHECK. Dorong siswa mencoba dan menjelaskan alasan. Gunakan scaffolding bertingkat: L0 gali pemikiran; L1 prompt metakognitif; L2 conceptual hint; L3 guided scaffolding; L4 worked explanation. Jawaban lengkap boleh diberikan setelah siswa mencoba/ketika scaffolding sebelumnya belum cukup, lalu lakukan comprehension check.
SELF-REFLECTION: bantu self-evaluation, error analysis, strategy evaluation, reflection, adaptation dan next goal.

Cakupan: prasyarat himpunan/pasangan berurutan/relasi; fungsi, domain, kodomain, range, input-output; diagram panah, pasangan berurutan, tabel, persamaan, grafik; nilai/aturan fungsi dan hubungan variabel; fungsi konstan/linear/pengantar kuadrat; one-to-one/many-to-one; pengayaan mapping, uniqueness, fungsi sebagai objek, komposisi/invers dengan bahasa SMP; aplikasi/pemodelan. Dorong hubungan antarrepresentasi.

Jika siswa langsung meminta jawaban, arahkan pemahaman/strategi dahulu lalu beri hint bertahap. Jika jawaban benar, cek alasan secara proporsional. Jika salah, diagnosis konsep/representasi/prosedur/perhitungan/interpretasi tanpa mempermalukan. Pertahankan student agency.'''

def db():
    c=sqlite3.connect(DB, check_same_thread=False)
    c.execute('''CREATE TABLE IF NOT EXISTS sessions(session_id TEXT PRIMARY KEY, student_id TEXT, goal TEXT, prior TEXT, strategy TEXT, started_at TEXT, reflection TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, ts TEXT, role TEXT, content TEXT, phase TEXT, process TEXT, scaffold INTEGER, topic TEXT)''')
    c.commit(); return c
conn=db()

def log(role, content, phase='', process='', scaffold=-1, topic=''):
    conn.execute('INSERT INTO messages(session_id,ts,role,content,phase,process,scaffold,topic) VALUES(?,?,?,?,?,?,?,?)',
                 (st.session_state.session_id, datetime.now().isoformat(timespec='seconds'), role, content, phase, process, scaffold, topic))
    conn.commit()

def classify(msg):
    m=msg.lower()
    topic='Fungsi'
    for k,v in [('domain','Domain'),('kodomain','Kodomain'),('range','Range'),('grafik','Grafik'),('relasi','Relasi'),('invers','Invers'),('komposisi','Komposisi')]:
        if k in m: topic=v; break
    direct=any(x in m for x in ['jawabannya','jawaban nya','langsung jawab','berapa hasil','berapa jawab'])
    attempt=any(x in m for x in ['saya coba','menurut saya','hasil saya','caranya','karena','=', 'jadi'])
    if direct and not attempt: return 'Performance','Help-Seeking',0,topic
    if attempt: return 'Performance','Self-Monitoring',1,topic
    return 'Performance','Help-Seeking',1,topic

def local_tutor(msg, scaffold, topic):
    # Fallback prototype so the app runs without an API key.
    if scaffold == 0:
        return f"Sebelum kita menuju jawabannya, coba ceritakan apa yang sudah kamu pahami tentang {topic.lower()} dari pertanyaan itu. Bagian mana yang paling membuatmu ragu?"
    if scaffold == 1:
        return f"Baik. Coba tentukan dulu konsep yang kamu perlukan untuk {topic.lower()} dan tuliskan satu langkah yang ingin kamu coba. Setelah itu kita periksa bersama apakah strateginya sudah sesuai."
    return "Coba gunakan petunjuk konsep yang paling dekat dengan soal, kerjakan satu langkah, lalu jelaskan alasanmu. Saya akan membantu dari langkah yang masih membingungkan."

def ai_reply(msg, phase, process, scaffold, topic):
    key=st.secrets.get('OPENAI_API_KEY','') if hasattr(st,'secrets') else ''
    if not key:
        return local_tutor(msg, scaffold, topic)
    try:
        from openai import OpenAI
        client=OpenAI(api_key=key)
        history=[]
        for x in st.session_state.messages[-10:]: history.append({'role':x['role'],'content':x['content']})
        instruction = SYSTEM_PROMPT + f"\nSTATUS INTERNAL: phase={phase}; process={process}; scaffold={scaffold}; topic={topic}. Respons 2-5 kalimat, satu langkah belajar utama."
        r=client.chat.completions.create(model=st.secrets.get('OPENAI_MODEL','gpt-4o-mini'), messages=[{'role':'system','content':instruction}]+history+[{'role':'user','content':msg}], temperature=.3)
        return r.choices[0].message.content
    except Exception as e:
        return local_tutor(msg, scaffold, topic) + "\n\n_(Mode prototipe lokal aktif.)_"

for k,v in {'stage':'home','messages':[],'session_id':'','student_id':'','goal':'','prior':'','strategy':''}.items():
    if k not in st.session_state: st.session_state[k]=v

st.title('🧠 SERLI-AI')
st.caption('Self-Regulated Learning Assistant for Understanding Functions • Prototype v1')

if st.session_state.stage=='home':
    st.info('Chatbot membantu siswa mengatur proses belajar melalui **Plan → Learn → Reflect**. Prototype ini tidak memasukkan mathematics anxiety ke dalam chatbot.')
    sid=st.text_input('Kode siswa', placeholder='Contoh: S001')
    if st.button('Mulai Belajar', type='primary', disabled=not sid.strip()):
        st.session_state.student_id=sid.strip(); st.session_state.session_id=str(uuid.uuid4()); st.session_state.stage='plan'; st.rerun()

elif st.session_state.stage=='plan':
    st.subheader('1. PLAN — Tentukan arah belajarmu')
    with st.form('plan'):
        goal=st.text_area('Apa yang ingin kamu pahami tentang fungsi hari ini?', placeholder='Contoh: Saya ingin memahami perbedaan domain, kodomain, dan range.')
        prior=st.text_area('Apa yang sudah kamu ketahui tentang hal tersebut?')
        strategy=st.text_area('Bagaimana kamu ingin mulai mempelajarinya?', placeholder='Contoh: dari contoh sederhana lalu mencoba soal.')
        ok=st.form_submit_button('Lanjut ke Belajar', type='primary')
    if ok and goal.strip():
        st.session_state.goal,st.session_state.prior,st.session_state.strategy=goal,prior,strategy
        conn.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?)',(st.session_state.session_id,st.session_state.student_id,goal,prior,strategy,datetime.now().isoformat(timespec='seconds'),'')); conn.commit()
        welcome=f"Targetmu hari ini: **{goal}**. Silakan mulai dengan pertanyaanmu. Saya akan membantu, tetapi kamu tetap memegang kendali proses belajarmu."
        st.session_state.messages=[{'role':'assistant','content':welcome}]; log('assistant',welcome,'Forethought','Goal Setting',-1,'Fungsi')
        st.session_state.stage='learn'; st.rerun()

elif st.session_state.stage=='learn':
    left,right=st.columns([1,3])
    with left:
        st.subheader('Target Saya')
        st.write(st.session_state.goal)
        st.markdown('**Progress**')
        st.write('✓ Plan\n\n● Learn\n\n○ Reflect')
        st.divider(); st.caption('Prinsip: pahami → coba → monitor → minta bantuan → revisi → cek.')
        if st.button('Selesai Belajar → Refleksi'):
            st.session_state.stage='reflect'; st.rerun()
    with right:
        st.subheader('2. LEARN — Tanya dan pikirkan bersama')
        for m in st.session_state.messages:
            with st.chat_message(m['role']): st.markdown(m['content'])
        q=st.chat_input('Tulis pertanyaan, pemikiran, atau langkah pengerjaanmu...')
        if q:
            st.session_state.messages.append({'role':'user','content':q}); log('user',q,'Performance','','','')
            phase,process,level,topic=classify(q)
            ans=ai_reply(q,phase,process,level,topic)
            st.session_state.messages.append({'role':'assistant','content':ans}); log('assistant',ans,phase,process,level,topic)
            st.rerun()

elif st.session_state.stage=='reflect':
    st.subheader('3. REFLECT — Lihat kembali proses belajarmu')
    st.write('Sebelum sesi selesai, pikirkan kembali apa yang terjadi selama belajar.')
    with st.form('reflection'):
        a=st.text_area('Apa yang sekarang kamu pahami tentang fungsi?')
        b=st.text_area('Bagian mana yang masih membingungkan atau sempat membuatmu salah?')
        c=st.text_area('Strategi atau bantuan apa yang paling membantumu?')
        d=st.text_area('Jika menghadapi masalah serupa tanpa AI, apa yang akan kamu lakukan?')
        e=st.text_area('Apa target belajarmu berikutnya?')
        done=st.form_submit_button('Selesaikan Sesi', type='primary')
    if done:
        ref=json.dumps({'understanding':a,'difficulty':b,'strategy':c,'without_ai':d,'next_goal':e},ensure_ascii=False)
        conn.execute('UPDATE sessions SET reflection=? WHERE session_id=?',(ref,st.session_state.session_id)); conn.commit(); log('user',ref,'Self-Reflection','Reflection',-1,'Fungsi')
        st.session_state.stage='done'; st.rerun()

elif st.session_state.stage=='done':
    st.success('Sesi belajar selesai. Data proses belajar dan percakapan telah tersimpan.')
    st.markdown('**Plan ✓  →  Learn ✓  →  Reflect ✓**')
    if st.button('Mulai sesi baru'):
        for k in ['messages','session_id','student_id','goal','prior','strategy']: st.session_state[k]=[] if k=='messages' else ''
        st.session_state.stage='home'; st.rerun()
