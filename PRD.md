PRD — ENGLISH SELF-ASSESSMENT QUIZ PLATFORM
Version: 1.0
Platform: Web Application
Framework: Streamlit
Programming Language: Python
Database: SQLite
Target User: Masyarakat umum
Primary Purpose: Self-assessment kemampuan Bahasa Inggris
Categories: Grammar, Reading, Listening
Difficulty: Easy, Medium, Hard
1. PRODUCT OVERVIEW
1.1 Nama Produk
Nama sementara:
English Self-Assessment Quiz
Nama dapat diganti kemudian sesuai branding aplikasi.
1.2 Deskripsi Produk
English Self-Assessment Quiz adalah aplikasi web interaktif yang memungkinkan pengguna mengukur kemampuan Bahasa Inggris secara mandiri melalui tiga kategori:
Grammar, Reading, dan Listening.
Pengguna terlebih dahulu mengisi identitas, kemudian bebas memilih kategori dan level yang ingin dikerjakan. Setelah menyelesaikan satu assessment, pengguna dapat memilih kategori dan level lain tanpa harus mengikuti urutan tertentu.
Aplikasi memberikan umpan balik langsung berupa:
jawaban benar/salah
efek suara
jawaban benar
pembahasan
skor
progress
Semua aktivitas assessment disimpan ke database sehingga pengguna dapat melihat riwayat hasil dan administrator dapat melihat data peserta serta performa soal.
2. PRODUCT GOALS
Aplikasi harus mampu:
Menyediakan self-assessment Bahasa Inggris yang mudah digunakan.
Menyediakan tiga kategori tes: Grammar, Reading, Listening.
Memungkinkan pengguna memilih kategori yang mereka inginkan terlebih dahulu.
Menyediakan tiga level: Easy, Medium, Hard.
Mengambil soal secara dinamis dari question bank.
Menghindari pengulangan soal dalam satu sesi.
Menyediakan feedback langsung.
Menyediakan audio feedback.
Menyimpan hasil assessment ke SQLite.
Menyediakan Admin Dashboard.
Memungkinkan admin mengimpor bank soal dari Word.
Memungkinkan admin menambah, mengedit, menonaktifkan, dan menghapus soal.
Memungkinkan admin menetapkan atau mengubah level soal.
Menghasilkan analitik performa pengguna dan soal.
Dapat dipublikasikan sebagai aplikasi web.
3. TARGET USERS
3.1 Public User
Masyarakat umum yang ingin:
berlatih Bahasa Inggris
mengetahui kemampuan mereka
mengukur perkembangan
mengidentifikasi kelemahan
mengulang assessment
Tidak harus memiliki akun kompleks pada versi pertama.
3.2 Administrator
Admin bertanggung jawab terhadap:
question bank
kategori
level
import soal
data peserta
hasil assessment
analitik
pengelolaan audio
pengelolaan konten.
4. USER JOURNEY
Alur utama pengguna:
LANDING PAGE
      ↓
IDENTITY FORM
      ↓
CATEGORY SELECTION
      ↓
LEVEL SELECTION
      ↓
QUIZ IN PROGRESS
      ↓
INSTANT FEEDBACK
      ↓
RESULT
      ↓
CHOOSE NEXT ACTION
      ├── Choose Another Level
      ├── Choose Another Category
      ├── Retry
      └── Finish
Contoh:
Grammar → Easy
      ↓
Result
      ↓
Listening → Medium
      ↓
Result
      ↓
Reading → Hard
Urutan sepenuhnya ditentukan pengguna.
5. LANDING PAGE
5.1 Elemen
Halaman utama berisi:
Logo / Nama aplikasi
English Self-Assessment
Tagline
Test. Practice. Understand. Improve.
Description
Penjelasan singkat mengenai tujuan aplikasi.
Tombol:
START SELF-ASSESSMENT
Link tambahan:
About
Instructions
Admin Login
6. IDENTITY PAGE
Pengguna mengisi:
Field	Required
Full Name	Yes
Email	Yes
Institution	No
Program/Occupation	No
Sistem otomatis menyimpan:
user ID
timestamp
device/session information yang diperlukan secara minimal.
Validasi:
nama tidak boleh kosong
email harus valid.
7. CATEGORY SELECTION
Setelah identitas, tampil:
Choose Your Test
Grammar
Mengukur pemahaman struktur dan tata bahasa.
Reading
Mengukur pemahaman bacaan.
Listening
Mengukur pemahaman materi audio.
Pengguna dapat memilih salah satu.
Tidak ada urutan wajib.
8. LEVEL SELECTION
Setiap kategori memiliki tiga level.
Easy
Fokus:
basic knowledge
simple structure
explicit information
direct understanding
Medium
Fokus:
application
contextual understanding
longer structure
moderate inference
Hard
Fokus:
complex structures
analysis
inference
more demanding context
9. RULE-BASED DIFFICULTY SYSTEM
Tidak menggunakan AI API pada versi pertama.
9.1 Prinsip
Setiap soal mempunyai field:
difficulty = easy / medium / hard
Level awal ditentukan oleh admin atau sistem memberikan rekomendasi berbasis aturan.
9.2 Grammar Criteria
Easy
satu konsep grammar
simple sentence
vocabulary umum
direct application
Medium
struktur lebih panjang
penerapan aturan
kombinasi konsep
distractor lebih mirip
Hard
complex sentence
multiple clauses
beberapa konsep sekaligus
analisis struktur
distractor sangat mirip
9.3 Reading Criteria
Level mempertimbangkan:
panjang teks
kompleksitas kalimat
vocabulary
jenis pertanyaan
kebutuhan inference
tingkat implicit meaning
9.4 Listening Criteria
Level mempertimbangkan:
durasi audio
kecepatan bicara
vocabulary
jumlah informasi
speaker interaction
explicit vs implicit meaning
inference.
10. IMPORT BANK SOAL WORD
Ini merupakan fitur inti.
10.1 Supported Format
Versi pertama:
.docx
Versi berikutnya:
.xlsx
.csv
10.2 Import Workflow
UPLOAD DOCX
     ↓
PARSE DOCUMENT
     ↓
DETECT QUESTIONS
     ↓
DETECT OPTIONS
     ↓
DETECT ANSWER
     ↓
DETECT EXPLANATION
     ↓
VALIDATE
     ↓
ASSIGN CATEGORY
     ↓
ASSIGN LEVEL
     ↓
ADMIN REVIEW
     ↓
APPROVE
     ↓
DATABASE
11. FORMAT SOAL WORD
Untuk stabilitas parser, format standar yang akan kita gunakan:
TOPIC: SUBJECT AND VERBS

QUESTION 1
The students ___ English every day.

A. study
B. studies
C. studying
D. studied

ANSWER: A

EXPLANATION:
The subject "students" is plural, so the correct verb is "study".
Namun parser sebaiknya dibuat cukup fleksibel untuk membaca file Word Anda yang sudah ada.
12. IMPORT VALIDATION
Setelah upload, sistem harus menampilkan:
Import Summary

Questions detected: 50
Valid questions: 47
Questions requiring review: 3
Contoh:
⚠ Question 17
Answer key missing

⚠ Question 29
Only 3 options detected

⚠ Question 41
Explanation missing
Admin tidak diperbolehkan mempublikasikan soal yang invalid sebelum diperbaiki atau ditandai sesuai aturan.
13. QUESTION BANK
Admin dapat mengakses seluruh soal.
Filter:
Category
Topic
Difficulty
Status
Source file
Search berdasarkan keyword.
Contoh:
No	Category	Topic	Level	Status
1	Grammar	Subject & Verbs	Easy	Active
2	Grammar	Subject & Verbs	Medium	Active
3	Reading	Main Idea	Medium	Active
4	Listening	Conversation	Hard	Active
14. QUESTION DATA MODEL
Untuk Grammar, Reading, dan Listening, setiap soal minimal memiliki:
question_id
category
topic
subtopic
question_type
question_text
option_a
option_b
option_c
option_d
correct_answer
explanation
difficulty
status
source_file
created_at
updated_at
Untuk Reading diperlukan tambahan:
passage_id
passage_text
Untuk Listening:
audio_id
audio_file
transcript
15. TIPE SOAL
Grammar
Versi pertama:
Multiple Choice
Format:
A, B, C, D.
Reading
Multiple Choice berdasarkan passage.
Jenis pertanyaan:
Main Idea
Detail
Vocabulary
Reference
Inference
Author's Purpose
Listening
Multiple Choice berdasarkan audio.
Jenis pertanyaan:
Main Idea
Detail
Meaning
Inference
Purpose
Speaker Attitude.
16. DYNAMIC QUESTION ENGINE
Ini fitur penting untuk memenuhi konsep kuis dinamis.
Ketika pengguna memilih:
Grammar → Medium
sistem:
Questions
    ↓
Filter category = Grammar
    ↓
Filter difficulty = Medium
    ↓
Remove recently used questions
    ↓
Randomize
    ↓
Select N questions
Misalnya tersedia:
200 Medium Grammar Questions
dan setting assessment:
20 questions
sistem memilih secara random 20 soal.
Pengguna berikutnya dapat memperoleh kombinasi yang berbeda.
17. QUESTION REPETITION LOGIC
Sistem harus menghindari:
Dalam satu assessment
Soal tidak boleh muncul dua kali.
Antar sesi pengguna
Sistem dapat mengurangi kemungkinan munculnya soal yang baru dikerjakan.
Table answers atau attempt_questions akan digunakan sebagai historical record.
Namun bila question bank terbatas, sistem diperbolehkan menggunakan kembali soal setelah seluruh soal tersedia telah digunakan.
18. JUMLAH SOAL
Default:
20 questions per assessment
Namun harus dibuat konfigurasi sehingga admin dapat mengubahnya menjadi:
10
15
20
25
30
atau nilai custom.
19. QUIZ INTERFACE
Contoh:
GRAMMAR — MEDIUM

Question 7 of 20

The students ___ already submitted
their assignments.

○ A. has
○ B. have
○ C. having
○ D. had

[SUBMIT ANSWER]

Progress
███████████░░░░░░░ 35%
20. INSTANT FEEDBACK
Setelah tombol submit:
Correct
✅ Correct!

🔊 Good Job!

Correct Answer: B

Explanation:
"Students" is plural, therefore
the correct auxiliary is "have".
Audio:
good_job.mp3
Incorrect
❌ Incorrect

🔊 Sorry, try again.

Your Answer: A
Correct Answer: B

Explanation:
"Students" is plural...
Audio:
sorry_try_again.mp3
21. AUDIO SYSTEM
Folder:
audio/
├── good_job.mp3
└── sorry_try_again.mp3
Untuk Listening:
audio/
└── listening/
    ├── listening_001.mp3
    ├── listening_002.mp3
    └── ...
Audio feedback digunakan untuk semua kategori.
Audio Listening merupakan bagian dari konten soal.
22. SCORING SYSTEM
Formula dasar:
Score =
(Correct Answers / Total Questions) × 100
Contoh:
20 soal
17 benar
17 / 20 × 100 = 85
Hasil:
85%
Data yang disimpan:
total questions
correct
incorrect
score
category
level
duration
timestamp.
23. RESULT PAGE
Contoh:
YOUR RESULT

Grammar — Medium

Score
85%

Correct
17 / 20

Incorrect
3 / 20

Accuracy
85%
Kemudian:
Next Action
[Try Easy]
[Try Medium]
[Try Hard]

[Choose Another Test]

[Finish Assessment]
24. SELF-ASSESSMENT SUMMARY
Jika pengguna telah mengerjakan beberapa assessment, sistem menampilkan:
MY SELF-ASSESSMENT

Grammar       85%
Reading       78%
Listening     82%
Grafik dapat dibuat menggunakan Plotly.
Informasi:
score
accuracy
number of attempts
strongest area
areas needing practice
Pernyataan sistem harus bersifat deskriptif, bukan diagnosis kemampuan formal.
25. HISTORY
Pengguna dapat melihat riwayat assessment dalam session/account sesuai implementasi versi aplikasi.
Contoh:
Date	Category	Level	Score
27-09-2026	Grammar	Easy	90
27-09-2026	Reading	Medium	78
28-09-2026	Listening	Easy	84
26. ADMIN LOGIN
Admin mempunyai halaman khusus.
Input:
Username / Email
Password
[LOGIN]
Password tidak boleh disimpan plaintext.
Gunakan:
bcrypt
untuk password hashing.
27. ADMIN DASHBOARD
Dashboard menampilkan:
TOTAL USERS
1,250

TOTAL ATTEMPTS
3,840

TOTAL QUESTIONS
650

ACTIVE QUESTIONS
620
Grafik:
user activity
assessment activity
category distribution
score distribution
question performance.
28. ADMIN USER MANAGEMENT
Admin dapat:
melihat user
search user
filter
membuka detail user
melihat assessment history.
Data:
Name
Email
Institution
Program
Registration Date
Total Attempts
Average Score
29. ADMIN QUESTION MANAGEMENT
Admin dapat:
Add
Menambahkan soal manual.
Edit
Mengubah soal.
Delete
Menghapus soal secara permanen bila diperlukan.
Deactivate
Lebih disarankan untuk penggunaan reguler:
Active
Inactive
Soal inactive tidak ditampilkan pada quiz.
Review
Memeriksa hasil import.
30. ADMIN IMPORT PAGE
Halaman:
IMPORT QUESTION BANK

Category:
[ Grammar ▼ ]

Topic:
[ Subject and Verbs ▼ ]

Upload:
[ Browse ]

[ Parse File ]

---------------------------------

50 questions detected

[ Preview ]

[ Validate ]

[ Import ]
Admin dapat menetapkan category ketika import.
31. LEVEL REVIEW
Setelah parsing:
No	Suggested Level	Final Level
1	Easy	Easy
2	Easy	Easy
3	Medium	Medium
4	Medium	Hard
5	Hard	Hard
Admin memiliki hak menentukan Final Level.
32. SOURCE FILE TRACKING
Setiap soal menyimpan:
source_file
Contoh:
Modul_Subject_and_Verbs_50_Soal.docx
Dengan demikian admin dapat mengetahui sumber soal.
33. OBSERVED DIFFICULTY
Selain level yang ditentukan admin, sistem menyimpan data performa nyata.
Contoh:
Assigned Level: Medium

Attempts: 500
Correct: 410
Accuracy: 82%
Admin dapat melihat:
Observed Accuracy = 82%
Aplikasi tidak otomatis mengubah level pada versi pertama.
Admin yang memutuskan apakah soal perlu dipindahkan levelnya.
34. QUESTION ANALYTICS
Admin dapat melihat:
Question Performance

Attempts
Correct
Incorrect
Accuracy
Contoh:
Question	Attempts	Accuracy
Q001	300	91%
Q002	290	75%
Q003	280	32%
Ini memungkinkan admin mengevaluasi kualitas bank soal.
35. DATABASE DESIGN
Table: users
id
name
email
institution
program
created_at
Table: admins
id
username
password_hash
role
created_at
Table: categories
id
name
description
Isi awal:
1 Grammar
2 Reading
3 Listening
Table: topics
id
category_id
name
description
Table: questions
id
category_id
topic_id
subtopic
question_type
question_text
option_a
option_b
option_c
option_d
correct_answer
explanation
difficulty
status
source_file
created_at
updated_at
Table: passages
id
title
passage_text
category_id
created_at
Table: audio_files
id
question_id
file_path
transcript
duration
created_at
Table: attempts
id
user_id
category_id
difficulty
total_questions
correct_answers
incorrect_answers
score
started_at
completed_at
duration_seconds
Table: attempt_questions
id
attempt_id
question_id
question_order
Table: answers
id
attempt_id
question_id
user_answer
correct_answer
is_correct
answered_at
36. RELATIONSHIP DATABASE
USERS
  │
  └──────< ATTEMPTS
              │
              ├──────< ATTEMPT_QUESTIONS
              │             │
              │             └──── QUESTION
              │
              └──────< ANSWERS

CATEGORIES
  │
  └──────< TOPICS
               │
               └──────< QUESTIONS

QUESTIONS
   │
   ├──── PASSAGES
   └──── AUDIO_FILES
37. FILE STORAGE STRUCTURE
Karena menggunakan SQLite, kita perlu memisahkan database dari aset.
data/
    english_assessment.db

uploads/
    imported_docs/
    
audio/
    feedback/
    listening/

assets/
    logo/
    images/
38. STRUKTUR FOLDER FINAL
Ini struktur yang saya rekomendasikan untuk Antigravity:
english_self_assessment/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── config/
│   ├── settings.py
│   └── constants.py
│
├── data/
│   └── english_assessment.db
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   ├── schema.py
│   ├── models.py
│   └── queries.py
│
├── pages/
│   ├── 01_Home.py
│   ├── 02_Identity.py
│   ├── 03_Test_Selection.py
│   ├── 04_Quiz.py
│   ├── 05_Result.py
│   ├── 06_History.py
│   │
│   ├── 90_Admin_Login.py
│   ├── 91_Admin_Dashboard.py
│   ├── 92_Admin_Users.py
│   ├── 93_Admin_Question_Bank.py
│   ├── 94_Admin_Import.py
│   ├── 95_Admin_Add_Edit_Question.py
│   ├── 96_Admin_Results.py
│   └── 97_Admin_Analytics.py
│
├── components/
│   ├── header.py
│   ├── footer.py
│   ├── navigation.py
│   ├── question_card.py
│   ├── answer_option.py
│   ├── progress_bar.py
│   ├── result_card.py
│   └── charts.py
│
├── services/
│   ├── quiz_engine.py
│   ├── scoring_service.py
│   ├── question_service.py
│   ├── user_service.py
│   ├── admin_service.py
│   └── analytics_service.py
│
├── utils/
│   ├── docx_parser.py
│   ├── excel_parser.py
│   ├── difficulty.py
│   ├── randomizer.py
│   ├── validators.py
│   ├── audio.py
│   ├── security.py
│   └── helpers.py
│
├── question_bank/
│   ├── grammar/
│   ├── reading/
│   └── listening/
│
├── uploads/
│   ├── imported_docs/
│   └── imported_excel/
│
├── audio/
│   ├── feedback/
│   │   ├── good_job.mp3
│   │   └── sorry_try_again.mp3
│   │
│   └── listening/
│
├── assets/
│   ├── logo/
│   ├── images/
│   └── icons/
│
└── tests/
    ├── test_database.py
    ├── test_parser.py
    ├── test_difficulty.py
    ├── test_quiz_engine.py
    └── test_scoring.py
39. FUNGSI SETIAP FOLDER
pages/
Semua halaman yang dilihat user dan admin.
components/
Komponen UI yang digunakan berulang.
services/
Logika utama aplikasi.
database/
Semua fungsi SQLite.
utils/
Utility seperti parsing Word, randomization, level calculation, validation.
audio/
Semua file suara.
uploads/
File yang diunggah admin.
assets/
Gambar dan identitas visual.
tests/
Pengujian sistem.
40. MAIN APPLICATION LOGIC
app.py menjadi entry point:
app.py
   ↓
Session Initialization
   ↓
Authentication / User Flow
   ↓
Page Navigation
Jangan memasukkan seluruh logic aplikasi ke app.py.
41. QUIZ ENGINE
File:
services/quiz_engine.py
Tanggung jawab:
mengambil soal
filtering category
filtering level
randomization
prevention duplicate
question order
submit answer
next question
finish assessment.
42. SCORING ENGINE
File:
services/scoring_service.py
Menghitung:
correct
incorrect
accuracy
score
dan menyimpan hasil.
43. WORD PARSER
File:
utils/docx_parser.py
Tugas:
DOCX
 ↓
Paragraphs
 ↓
Question Detector
 ↓
Option Detector
 ↓
Answer Detector
 ↓
Explanation Detector
 ↓
Structured Question
44. DIFFICULTY ENGINE
File:
utils/difficulty.py
Tugas:
memberikan suggested_level.
Tetapi:
Suggested Level
       ↓
Admin Review
       ↓
Final Level
Final Level yang tersimpan di database adalah keputusan admin.
45. SECURITY
Minimum requirement:
password hash
session control
admin route protection
file upload validation
allowed file extensions
size limit
input validation
SQL parameterization.
Jangan menggunakan SQL string concatenation untuk input user.
46. NON-FUNCTIONAL REQUIREMENTS
Performance
Aplikasi harus mampu:
memuat halaman dengan cepat
mengambil soal dari database secara efisien
tidak melakukan operasi berat berulang.
Reliability
tidak kehilangan hasil assessment
transaksi database harus aman
backup database harus dapat dilakukan.
Usability
UI harus:
sederhana
jelas
responsive
mudah dipahami pengguna umum.
Accessibility
Sedapat mungkin:
font mudah dibaca
kontras cukup
tombol jelas
audio memiliki kontrol play/pause
jangan mengandalkan warna saja untuk menunjukkan jawaban.
47. RESPONSIVE DESIGN
Target:
Desktop
Optimal.
Tablet
Didukung.
Mobile
Harus tetap dapat digunakan, terutama:
identitas
memilih kategori
kuis
listening
result.
Untuk aplikasi publik, mobile responsiveness harus menjadi perhatian sejak awal.
48. ADMIN SETTINGS
Admin dapat mengatur:
Default Questions per Assessment
Enable/Disable Category
Enable/Disable Difficulty
Audio Feedback
Question Randomization
Show Explanation Immediately
Contoh:
Questions per test: 20
Randomize: ON
Immediate feedback: ON
Sound effect: ON
49. STATUS QUESTION
Setiap soal:
Draft
Active
Inactive
Archived
Draft
Belum dipublikasikan.
Active
Digunakan dalam quiz.
Inactive
Tidak digunakan tetapi masih ada di database.
Archived
Tidak digunakan lagi namun tetap tersimpan.
50. IMPORT HISTORY
Table tambahan:
import_history
Field:
id
file_name
category
total_detected
total_imported
total_failed
imported_by
imported_at
Sehingga admin dapat mengetahui asal question bank.
51. EXAMPLE USER FLOW
User enters application
        ↓
Start Self Assessment
        ↓
Fill Name + Email
        ↓
Choose Grammar
        ↓
Choose Easy
        ↓
20 random questions
        ↓
Q1
        ↓
Answer
        ↓
Feedback + Audio
        ↓
Q2
        ↓
...
        ↓
Q20
        ↓
Result
        ↓
Score 85%
        ↓
Choose Listening
        ↓
Medium
52. EXAMPLE ADMIN FLOW
Admin Login
     ↓
Dashboard
     ↓
Import Question Bank
     ↓
Upload Word
     ↓
Parser
     ↓
50 Questions
     ↓
Validation
     ↓
Set Category
     ↓
Suggested Difficulty
     ↓
Admin Review
     ↓
Approve
     ↓
Active Question Bank
53. ACCEPTANCE CRITERIA
Aplikasi dianggap memenuhi MVP jika:
User
pengguna dapat mengisi identitas
pengguna dapat memilih Grammar/Reading/Listening
pengguna dapat memilih Easy/Medium/Hard
soal tampil secara dinamis
tidak ada duplicate dalam satu attempt
jawaban dapat dinilai otomatis
feedback muncul
audio bekerja
pembahasan muncul
skor dihitung
hasil tersimpan.
Admin
admin dapat login
admin dapat melihat dashboard
admin dapat melihat pengguna
admin dapat import Word
parser dapat membaca soal
admin dapat review hasil parsing
admin dapat menetapkan level
admin dapat menambah/edit soal
admin dapat mengaktifkan/nonaktifkan soal
admin dapat melihat hasil assessment.
54. MVP — VERSI PERTAMA
Saya sangat menyarankan Antigravity jangan langsung membuat semua fitur di atas sekaligus.
MVP Phase 1
Streamlit
SQLite
Database schema
Home
User identity
Grammar
Easy/Medium/Hard
Quiz engine
Score
Phase 2
Reading
Listening
Audio
Phase 3
Admin Login
Dashboard
Question Bank
Phase 4
DOCX Import
Validation
Difficulty Assignment
Phase 5
History
Analytics
Question Performance
Phase 6
UI refinement
Responsive design
Testing
Deployment
55. IMPORTANT PRODUCT PRINCIPLE
Ada satu keputusan arsitektur yang perlu kita tetapkan sejak awal:
AI bukan komponen wajib pada versi 1.
Aplikasi tetap harus berfungsi penuh tanpa API AI.
Kemampuan seperti:
question selection
scoring
difficulty
randomization
feedback
database
analytics
semuanya dilakukan oleh Python + SQLite + rules.
AI dapat ditambahkan pada versi berikutnya sebagai fitur tambahan seperti:
AI Question Generator
AI Explanation Assistant
AI Content Review
tetapi tidak menjadi ketergantungan sistem.
56. STACK TEKNOLOGI FINAL
LANGUAGE
Python

WEB FRAMEWORK
Streamlit

DATABASE
SQLite

WORD IMPORT
python-docx

EXCEL
openpyxl

DATA PROCESSING
pandas

CHARTS
plotly

PASSWORD SECURITY
bcrypt

EMAIL VALIDATION
email-validator

IMAGE PROCESSING
Pillow
57. PROJECT DIRECTORY FINAL
Secara singkat:
english_self_assessment/
│
├── app.py
├── requirements.txt
│
├── config/
├── data/
├── database/
├── pages/
├── components/
├── services/
├── utils/
├── question_bank/
├── uploads/
├── audio/
├── assets/
└── tests/
58. ARAHAN PEMBANGUNAN DI ANTIGRAVITY
Untuk menghindari Antigravity menghasilkan kode yang terlalu besar dan sulit diperbaiki, PRD ini sebaiknya dijadikan master specification, tetapi implementasinya dilakukan bertahap.
Urutan yang paling aman:
1. Initialize Project
       ↓
2. Database
       ↓
3. User Flow
       ↓
4. Grammar Quiz
       ↓
5. Reading
       ↓
6. Listening
       ↓
7. Audio
       ↓
8. Admin
       ↓
9. Word Import
       ↓
10. Difficulty Engine
       ↓
11. Analytics
       ↓
12. Testing
       ↓
13. Deployment