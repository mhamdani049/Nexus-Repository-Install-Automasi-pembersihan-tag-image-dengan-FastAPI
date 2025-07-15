Nexus Repository - Install & Automasi Pembersihan Tag Image dengan FastAPI

Deskripsi:  
Aplikasi ini berfungsi untuk mengotomasi proses pembersihan tag image yang sudah tidak diperlukan di Nexus Repository menggunakan aplikasi berbasis FastAPI. Dengan ini, Anda dapat menjaga repository lebih bersih dari tag-tag image yang tidak digunakan, sehingga menghemat ruang penyimpanan dan memudahkan manajemen repository.

Langkah-langkah Menjalankan Aplikasi

1. Clone Repository  
Clone kode sumber dari GitHub:  
git clone https://github.com/mhamdani049/Nexus-Repository-Install-Automasi-pembersihan-tag-image-dengan-FastAPI.git  
cd Nexus-Repository-Install-Automasi-pembersihan-tag-image-dengan-FastAPI

2. Konfigurasi Environment  
Buat file .env di root folder project untuk menyimpan konfigurasi Nexus Repository Anda:  
NEXUS_URL=http://your-nexus-host:8081  
NEXUS_USERNAME=admin  
NEXUS_PASSWORD=yourpassword  
Gantilah sesuai dengan detail Nexus Repository Anda.

3. Instalasi Dependencies  
Pastikan Python 3.8+ sudah terinstal.  
Install dependencies yang dibutuhkan dengan perintah:  
pip install -r requirements.txt

4. Jalankan Server FastAPI  
Gunakan perintah berikut untuk menjalankan aplikasi FastAPI:  
uvicorn main:app --host 0.0.0.0 --port 8000 --reload  
Ini akan menjalankan API pada http://localhost:8000

Penggunaan Endpoint Utama

POST /repositories/{repository}/cleanup-image-keep-new-tag  
Fungsi untuk membersihkan tag tag lama pada suatu repository tertentu, dengan opsi mempertahankan sejumlah tag terbaru.  
Request body contoh:  
{
  "keep_last_tag": 5
}  
Artinya sistem akan mempertahankan 5 tag terbaru dan menghapus tag-tag image yang lebih lama dari itu.

---

Opsi Menggunakan Docker (Opsional)

Build Docker Image  
Jika Anda ingin menjalankan aplikasi via Docker:  
docker build -t nexus-cleanup-fastapi .

Jalankan Docker Container  
docker run -d -p 8000:8000 --env-file .env nexus-cleanup-fastapi

Jika Ada docker-compose.yml  
Jalankan dengan:  
docker-compose up -d

Catatan Penting

- Pastikan Nexus Repository API dapat diakses dari mesin yang menjalankan aplikasi ini.  
- Simpan kredensial sensitif seperti username dan password hanya di file .env, dan jangan commit file ini ke GitHub.  
- FastAPI menyediakan fitur hot reload untuk memudahkan pengembangan dengan flag --reload.  

Semoga dokumentasi ini membantu Anda dan pengguna lain dalam menjalankan serta memanfaatkan aplikasi automasi pembersihan tag image Nexus Repository ini.
