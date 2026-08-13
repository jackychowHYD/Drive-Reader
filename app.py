import os
import io
import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'service_account.json'

@st.cache_resource
def authenticate_google_drive():
    """進行身分驗證：優先讀取 Streamlit Cloud Secrets，若無則讀取本地 service_account.json"""
    creds = None
    
    # 1. 優先讀取 Streamlit Cloud 上的 Secrets 設定
    if "gcp_service_account" in st.secrets:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
    # 2. 本地電腦開發環境 (讀取 service_account.json)
    elif os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
    else:
        st.error("找不到驗證金鑰！請在 Streamlit Cloud 設定 Secrets，或在本地放置 service_account.json。")
        return None

    return build('drive', 'v3', credentials=creds)

def get_all_accessible_folders(service):
    """動態獲取服務帳號有權限存取的所有資料夾"""
    query = "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(
        q=query, 
        fields="files(id, name)",
        pageSize=100
    ).execute()
    folders = results.get('files', [])
    # 按照資料夾名稱排序
    folders = sorted(folders, key=lambda x: x['name'])
    return {f['name']: f['id'] for f in folders}

def list_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed = false and mimeType != 'application/vnd.google-apps.folder'"
    results = service.files().list(
        q=query, 
        fields="files(id, name, mimeType, size, webViewLink, webContentLink)"
    ).execute()
    return results.get('files', [])

def download_file_bytes(service, file_id, mime_type):
    if mime_type == 'application/vnd.google-apps.document':
        request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
    elif mime_type == 'application/vnd.google-apps.spreadsheet':
        request = service.files().export_media(
            fileId=file_id, 
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        request = service.files().get_media(fileId=file_id)

    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    
    file_stream.seek(0)
    return file_stream.read()

def main():
    st.set_page_config(page_title="Google Drive 體系文檔管理員", layout="wide")
    st.title("📁 Google Drive 體系文檔預覽與下載系統")

    service = authenticate_google_drive()
    if not service:
        st.stop()

    # 自動動態抓取所有共用資料夾
    with st.spinner("正在讀取可存取的資料夾..."):
        folder_dict = get_all_accessible_folders(service)

    if not folder_dict:
        st.warning("目前服務帳號找不到任何可存取的資料夾。請確定已在 Google Drive 將資料夾「共用」給服務帳號 Email！")
        return

    st.sidebar.header("選單")
    selected_folder_name = st.sidebar.selectbox("請選擇目標資料夾：", list(folder_dict.keys()))

    if selected_folder_name:
        folder_id = folder_dict[selected_folder_name]
        st.subheader(f"📂 目前資料夾：`{selected_folder_name}`")

        files = list_files_in_folder(service, folder_id)

        if not files:
            st.info("該資料夾內目前沒有檔案。")
            return

        df_data = [{"檔案名稱": f['name'], "類型": f['mimeType'].split('.')[-1], "檔案 ID": f['id']} for f in files]
        st.dataframe(pd.DataFrame(df_data), use_container_width=True)

        st.markdown("---")
        st.subheader("📄 檔案預覽與下載")

        file_dict = {f['name']: f for f in files}
        selected_filename = st.selectbox("請選擇要查看或下載的檔案：", list(file_dict.keys()))

        if selected_filename:
            selected_file = file_dict[selected_filename]
            f_id = selected_file['id']
            f_mime = selected_file['mimeType']
            f_link = selected_file.get('webViewLink', '')

            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown(f"**檔名:** {selected_file['name']}")
                st.markdown(f"**MIME 類型:** `{f_mime}`")
                
                try:
                    file_bytes = download_file_bytes(service, f_id, f_mime)
                    st.download_button(
                        label="⬇️ 下載此檔案",
                        data=file_bytes,
                        file_name=selected_filename,
                        mime="application/octet-stream"
                    )
                except Exception as e:
                    st.error(f"下載失敗: {str(e)}")

                if f_link:
                    st.markdown(f"[🔗 在 Google Drive 中開啟]({f_link})")

            with col2:
                st.markdown("### 👁️ 檔案預覽")
                if f_link:
                    embed_url = f_link.replace('/view?usp=drivesdk', '/preview').replace('/view', '/preview')
                    st.components.v1.iframe(embed_url, height=500, scrolling=True)
                else:
                    st.info("此檔案格式不支援線上預覽，請使用下載按鈕。")

if __name__ == '__main__':
    main()