import os
import time
import requests
from typing import List, Dict, Any, Optional

BUFFER_GRAPHQL_ENDPOINT = "https://api.buffer.com"
CATBOX_API_ENDPOINT = "https://catbox.moe/user/api.php"

def upload_to_catbox(video_path: str, timeout: int = 180) -> str:
    """
    Upload file video lên Catbox để nhận Direct Public URL (0 VNĐ, không cần thẻ/tài khoản).
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Không tìm thấy file video: {video_path}")

    filename = os.path.basename(video_path)
    print(f"[BufferService] Đang tải video '{filename}' ({os.path.getsize(video_path):,} bytes) lên máy chủ trung chuyển (0đ)...")

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    headers = {"User-Agent": USER_AGENT}

    # 1. Thử Catbox
    try:
        with open(video_path, "rb") as f:
            resp = requests.post(
                CATBOX_API_ENDPOINT,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (filename, f, "video/mp4")},
                headers=headers,
                timeout=timeout
            )
        if resp.status_code == 200 and resp.text.strip().startswith("http"):
            direct_url = resp.text.strip()
            print(f"[BufferService] Direct Video URL (Catbox): {direct_url}")
            return direct_url
        print(f"[BufferService] Catbox phản hồi ({resp.status_code}): {resp.text.strip()}. Chuyển sang cổng phụ Uguu...")
    except Exception as ce:
        print(f"[BufferService] Catbox error: {ce}. Chuyển sang Uguu...")

    # 2. Cổng dự phòng Uguu.se (Miễn phí, Direct link .mp4, hỗ trợ máy chủ Linux)
    try:
        with open(video_path, "rb") as f:
            resp = requests.post(
                "https://uguu.se/upload",
                files={"files[]": (filename, f, "video/mp4")},
                headers=headers,
                timeout=timeout
            )
        if resp.status_code == 200:
            res_data = resp.json()
            if res_data.get("success") and res_data.get("files"):
                direct_url = res_data["files"][0]["url"]
                print(f"[BufferService] Direct Video URL (Uguu): {direct_url}")
                return direct_url
    except Exception as ue:
        print(f"[BufferService] Uguu error: {ue}")

    raise RuntimeError("Không thể tải video lên máy chủ trung chuyển. Vui lòng kiểm tra lại kết nối mạng.")

def get_connected_tiktok_channels(access_token: str) -> List[Dict[str, str]]:
    """
    Truy vấn danh sách tất cả các kênh TikTok đã kết nối với tài khoản Buffer.
    """
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json"
    }

    # 1. Lấy danh sách organizations
    org_query = "{ account { organizations { id name } } }"
    r_org = requests.post(BUFFER_GRAPHQL_ENDPOINT, json={"query": org_query}, headers=headers, timeout=20)
    r_org_data = r_org.json()

    if "errors" in r_org_data:
        raise RuntimeError(f"Lỗi xác thực Buffer API: {r_org_data['errors']}")

    orgs = r_org_data.get("data", {}).get("account", {}).get("organizations", [])
    if not orgs:
        raise RuntimeError("Không tìm thấy Organization nào trong tài khoản Buffer.")

    tiktok_channels = []
    # 2. Truy vấn kênh trong từng organization
    for org in orgs:
        org_id = org["id"]
        ch_query = """
        query GetChannels($input: ChannelsInput!) {
            channels(input: $input) {
                id
                name
                service
            }
        }
        """
        r_ch = requests.post(
            BUFFER_GRAPHQL_ENDPOINT,
            json={"query": ch_query, "variables": {"input": {"organizationId": org_id}}},
            headers=headers,
            timeout=20
        )
        ch_data = r_ch.json()
        channels = ch_data.get("data", {}).get("channels", [])
        for ch in channels:
            if ch.get("service") == "tiktok":
                tiktok_channels.append({
                    "id": ch["id"],
                    "name": ch.get("name", "TikTok Channel"),
                    "service": "tiktok"
                })

    return tiktok_channels

def post_video_to_buffer_tiktok(
    access_token: str,
    channel_ids: List[str],
    video_url: str,
    caption: str,
    mode: str = "shareNow",
    due_at: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Đăng video lên các kênh TikTok qua Buffer GraphQL API.
    Mode: 'shareNow' (Đăng ngay), 'customScheduled' (Hẹn giờ chính xác), hoặc 'addToQueue' (Thêm vào hàng đợi)
    """
    headers = {
        "Authorization": f"Bearer {access_token.strip()}",
        "Content-Type": "application/json"
    }

    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            text
            status
          }
        }
        ... on NotFoundError { message }
        ... on UnauthorizedError { message }
        ... on UnexpectedError { message }
        ... on RestProxyError { message }
        ... on LimitReachedError { message }
        ... on InvalidInputError { message }
      }
    }
    """

    results = []
    for ch_id in channel_ids:
        actual_mode = "customScheduled" if due_at else mode
        print(f"[BufferService] Đang gửi bài viết tới TikTok Channel ID: {ch_id} (Mode: {actual_mode}, dueAt: {due_at})...")
        
        input_data = {
            "channelId": ch_id,
            "mode": actual_mode,
            "schedulingType": "automatic",
            "needsApproval": False,
            "text": caption,
            "assets": [
                {
                    "video": {
                        "url": video_url
                    }
                }
            ]
        }
        if due_at:
            input_data["dueAt"] = due_at

        payload = {
            "query": mutation,
            "variables": {
                "input": input_data
            }
        }

        try:
            resp = requests.post(BUFFER_GRAPHQL_ENDPOINT, json=payload, headers=headers, timeout=40)
            res_json = resp.json()

            # Nếu shareNow bị hạn chế, tự động fallback sang addToQueue
            errors = res_json.get("errors", [])
            data_res = res_json.get("data", {}).get("createPost", {})

            if "message" in data_res and mode == "shareNow":
                print(f"[BufferService] 'shareNow' báo '{data_res['message']}', thử chuyển sang 'addToQueue'...")
                payload["variables"]["input"]["mode"] = "addToQueue"
                resp = requests.post(BUFFER_GRAPHQL_ENDPOINT, json=payload, headers=headers, timeout=40)
                res_json = resp.json()
                data_res = res_json.get("data", {}).get("createPost", {})

            print(f"[BufferService] Phản hồi kênh {ch_id}: {res_json}")
            results.append({"channelId": ch_id, "response": res_json})
        except Exception as ex:
            print(f"[BufferService] Lỗi khi gửi tới kênh {ch_id}: {ex}")
            results.append({"channelId": ch_id, "error": str(ex)})

    return results

if __name__ == "__main__":
    import sys
    token = "-9ESK8oz-t0w6unWFrEALs2wX0THZQWPnTGKKuj0KTx"
    chans = get_connected_tiktok_channels(token)
    print("TikTok Channels:", chans)
