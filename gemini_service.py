import os
import sys
import json
import random
import time
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple, List

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Rich Category & Subtopic taxonomies (16 Categories + Custom)
TOPIC_CATEGORIES: Dict[str, List[str]] = {
    "🧪 Lầm Tưởng Đời Sống & Sự Thật Khoa Học": [
        "Sạc điện thoại qua đêm vs Ngắt sạc khi đầy 80%",
        "Ngồi gần màn hình gây cận thị vs Chỉ gây mỏi mắt tạm thời",
        "Uống nước đá gây viêm họng vs Nước đá giảm sưng đau",
        "Nuốt bã kẹo cao su tồn tại 7 năm vs Đào thải sau vài ngày",
        "Đọc sách trong bóng tối hỏng mắt vs Không làm thay đổi thị lực",
        "Ăn cà rốt giúp mắt sáng như cú vọ vs Tác dụng thực tế"
    ],
    "🥑 Tranh Luận Dinh Dưỡng & Ăn Uống Lành Mạnh": [
        "Uống nước chanh ấm buổi sáng vs Nước lọc ấm",
        "Ăn 2 quả trứng mỗi ngày vs Chỉ ăn lòng trắng",
        "Đường cát trắng vs Mật ong nguyên chất",
        "Ăn thịt bò đỏ vs Ăn ức gà tăng cơ",
        "Nhịn ăn gián đoạn 16/8 vs Ăn đủ 3 bữa đúng giờ",
        "Sữa tươi nguyên kem vs Sữa hạt thực vật"
    ],
    "🍜 Ẩm thực & Món ăn Đặc sản": [
        "Cơm tấm Sài Gòn vs Phở bò Hà Nội",
        "Trà sữa trân châu vs Cà phê muối",
        "Lẩu Haidilao vs Lẩu Manwah",
        "Bún bò Huế vs Bún chả Hà Nội",
        "Bánh mì Sài Gòn vs Bánh mì Hội An",
        "Bò Wagyu nướng vs Bò tơ Tây Ninh"
    ],
    "🏢 Tranh Cãi Công Sở & Tư Duy Đi Làm": [
        "Đúng 5h chiều tắt máy đi về vs Ở lại làm thêm cống hiến",
        "Làm việc 10 năm tại một công ty vs Nhảy việc 2 năm một lần",
        "Thân thiết với đồng nghiệp như bạn thân vs Giữ khoảng cách công việc",
        "Làm việc Remote tại nhà vs Đến văn phòng giao tiếp trực tiếp",
        "Nhận việc ngoài làm Freelance vs Tập trung 100% thăng tiến công ty"
    ],
    "💳 Thói Quen Tiêu Dùng & Quản Lý Tiền Bạc": [
        "Mua đồ rẻ thay liên tục vs Mua đồ hiệu đắt dùng 10 năm",
        "Mua trả góp 0% giữ tiền kinh doanh vs Gom đủ tiền mặt mới mua",
        "Tự nấu ăn tiết kiệm vs Ăn ngoài dành thời gian kiếm tiền",
        "Đi du lịch trải nghiệm tuổi trẻ vs Tiết kiệm mua bảo hiểm sớm",
        "Dùng thẻ tín dụng hoàn tiền vs Chỉ dùng tiền mặt kiểm soát chi tiêu"
    ],
    "💰 Quyết Định Tài Chính & Đầu Tư Lớn": [
        "Mua nhà trả góp tuổi 30 vs Thuê nhà để tiền đầu tư",
        "Gửi tiết kiệm ngân hàng lấy lãi vs Mua vàng tích lũy lâu dài",
        "Học Đại học danh tiếng vs Đi làm sớm tích lũy kinh nghiệm thực chiến",
        "Sống và lập nghiệp tại Sài Gòn vs Hà Nội",
        "Khởi nghiệp kinh doanh riêng vs Làm quản lý cấp cao công ty lớn"
    ],
    "🎭 Tâm Lý Học Hành Vi & Bẫy Cảm Xúc": [
        "Người hay im lặng khi tức giận vs Người nói thẳng xả hết cơn giận",
        "Người luôn đúng giờ vs Người hay trễ 5 phút",
        "Nói thẳng nói thật mất lòng vs Khéo léo giữ thể diện cho đối phương",
        "Người thích ở một mình hướng nội vs Người nghiện tiệc tùng hướng ngoại",
        "Kìm nén cảm xúc để mạnh mẽ vs Bộc lộ yếu đuối để giải tỏa"
    ],
    "📱 Công nghệ & Thiết bị Điện tử": [
        "iPhone vs Samsung",
        "iPhone 15 Pro Max vs Samsung Galaxy S24 Ultra",
        "MacBook M3 vs Laptop Windows Cao Cấp",
        "AirPods Pro 2 vs Sony WF-1000XM5",
        "iPad Pro M4 vs Samsung Galaxy Tab S9 Ultra",
        "Apple Watch Ultra 2 vs Garmin Fenix 7 Pro"
    ],
    "🤖 Phần Mềm, Ứng Dụng & Công Cụ AI": [
        "ChatGPT 4o vs Claude 3.5 Sonnet",
        "Windows 11 vs macOS Sonoma",
        "Adobe Premiere Pro vs CapCut PC",
        "Midjourney v6 vs DALL-E 3",
        "iPhone iOS vs Android Thuần"
    ],
    "💻 Tương Lai Việc Làm: AI vs Kỹ Năng Con Người": [
        "Học vẽ tranh mỹ thuật truyền thống vs Học vẽ Prompt AI",
        "Bác sĩ chẩn đoán lâm sàng vs Trí tuệ nhân tạo đọc phim X-Quang",
        "Kỹ năng lập trình viết code vs Kỹ năng giao tiếp đàm phán",
        "Biên kịch nội dung con người vs AI tạo kịch bản tự động",
        "Dịch thuật viên chuyên nghiệp vs Công cụ dịch AI thời gian thực"
    ],
    "🚗 Xe cộ & Phương tiện Di chuyển": [
        "Xe máy điện VinFast vs Xe máy xăng",
        "Honda SH 160i vs Honda Air Blade 160",
        "Ô tô điện Tesla Model 3 vs BYD Seal",
        "VinFast VF8 vs Hyundai Santa Fe",
        "Xe bán tải Ford Ranger vs Toyota Hilux"
    ],
    "🎮 Game & Thiết Bị Giải Trí": [
        "PlayStation 5 vs Xbox Series X",
        "Liên Quân Mobile vs Liên Minh Tốc Chiến",
        "Nintendo Switch OLED vs Steam Deck",
        "Màn hình Gaming 240Hz vs Màn hình Đồ họa 4K",
        "Chơi game PC Desktop vs Chơi game Laptop Gaming"
    ],
    "👨‍👩‍👧 Tranh Luận Nuôi Dạy Con & Gia Đình": [
        "Cho con dùng iPad học sớm vs Cấm tuyệt đối thiết bị điện tử",
        "Khen ngợi động viên tự tin vs Nghiêm khắc rèn luyện kỷ luật thép",
        "Để con tự ngã tự đứng dậy vs Luôn theo sát bảo bọc an toàn",
        "Định hướng nghề nghiệp cho con vs Để con tự do chọn đam mê",
        "Cho con học trường quốc tế vs Trường công lập chuyên chọn"
    ],
    "🐾 Thú Cưng: Nuôi Dạy & So Sánh Giống Loài": [
        "Nuôi Chó Corgi vs Chó Poodle",
        "Nuôi Mèo Anh lông ngắn vs Mèo Ta",
        "Nuôi Chó Cảnh vs Nuôi Mèo Cảnh",
        "Nuôi Chó Alaska vs Chó Husky Ngáo",
        "Nuôi Mèo Chân Ngắn Munchkin vs Mèo Bengal"
    ],
    "🐕 Giải Mã Hành Vi Thú Cưng & Bí Ẩn Động Vật": [
        "Mèo chớp mắt chậm: Buồn ngủ hay đang tỏ tình yêu chủ?",
        "Chó vẫy đuôi: Luôn là mừng rỡ hay có lúc đang cảnh giác tấn công?",
        "Nuôi chó thả rông sân vườn vs Nuôi trong phòng máy lạnh",
        "Loài mèo uống sữa bò: Tốt cho sức khỏe hay gây tiêu chảy dị ứng?",
        "Cá mập tấn công người: Bản năng săn mồi hay do nhầm lẫn hình bóng?"
    ],
    "🌍 Nghịch Lý Địa Lý & Văn Hóa Thế Giới": [
        "Sa mạc Sahara: Nóng rát ban ngày vs Đóng băng ban đêm",
        "Nước máy vòi uống ở Singapore vs Nước khoáng đóng chai cao cấp",
        "Văn hóa đúng giờ ở Nhật Bản vs Văn hóa thư thái ở châu Âu",
        "Thành phố đắt đỏ nhất thế giới: New York vs Tokyo vs Singapore",
        "Thói quen ăn bằng tay ở Ấn Độ vs Dùng đũa ở Đông Á"
    ],
    "📜 Bí Ẩn Lịch Sử & Lầm Tưởng Cổ Nhân": [
        "Kim tự tháp Ai Cập: Nô lệ bị ép buộc vs Thợ lành nghề được trả lương",
        "Áo giáp sắt Hiệp sĩ Trung Cổ: Nặng nề bất tiện vs Cực kỳ linh hoạt",
        "Vạn Lý Trường Thành: Nhìn thấy từ vũ trụ hay chỉ là lời đồn?",
        "Chiếc gương soi thời cổ đại: Làm bằng đồng thau hay bạc nguyên chất?",
        "Thanh kiếm Samurai Katana vs Kiếm dài Hiệp sĩ phương Tây"
    ],
    "✍️ Tự nhập chủ đề tùy biến": []
}

CATEGORY_ANGLES: Dict[str, List[str]] = {
    "🧪 Lầm Tưởng Đời Sống & Sự Thật Khoa Học": [
        "So sánh về Cơ chế khoa học thực tế và Thói quen truyền miệng",
        "So sánh về Tác hại ngộ nhận và Lợi ích thực sự đã được kiểm chứng",
        "Bóc trần sự thật khoa học đối lập với niềm tin số đông"
    ],
    "🥑 Tranh Luận Dinh Dưỡng & Ăn Uống Lành Mạnh": [
        "So sánh về Giá trị calo, Chỉ số đường huyết & Độ lành mạnh",
        "So sánh về Tác động đến vóc dáng, Khả năng hấp thụ & Chuyển hóa",
        "Góc nhìn khoa học dinh dưỡng thực tế sau thời gian dài áp dụng"
    ],
    "🍜 Ẩm thực & Món ăn Đặc sản": [
        "So sánh về Hương vị đặc trưng, Nước dùng & Sự đậm đà",
        "So sánh về Giá trị dinh dưỡng, Calo & Độ lành mạnh",
        "So sánh về Độ phổ biến, Văn hóa ẩm thực & Độ phủ sóng",
        "So sánh về Sự phong phú của Topping & Đồ ăn kèm"
    ],
    "🏢 Tranh Cãi Công Sở & Tư Duy Đi Làm": [
        "So sánh về Cơ hội thăng tiến lâu dài vs Chất lượng cuộc sống hiện tại",
        "So sánh về Khả năng tích lũy kinh nghiệm vs Áp lực tinh thần",
        "Góc nhìn thực tế giữa cống hiến hết mình và làm việc thông minh"
    ],
    "💳 Thói Quen Tiêu Dùng & Quản Lý Tiền Bạc": [
        "So sánh về Giá trị sử dụng lâu dài và Tổng chi phí khấu hao",
        "So sánh về Tự do tâm trí và Khả năng tích lũy dòng tiền",
        "Trải nghiệm thực tế giữa chi tiêu hưởng thụ và tiết kiệm phòng thủ"
    ],
    "💰 Quyết Định Tài Chính & Đầu Tư Lớn": [
        "So sánh về Tỷ suất sinh lời & Khả năng phòng thủ rủi ro tài chính",
        "So sánh về Tự do tinh thần, Áp lực cuộc sống & Chất lượng trải nghiệm",
        "Bài toán dòng tiền sau 5 năm đến 10 năm thực tế"
    ],
    "🎭 Tâm Lý Học Hành Vi & Bẫy Cảm Xúc": [
        "So sánh về Tác động tâm lý sâu xa và Động cơ hành vi vô thức",
        "So sánh về Khả năng giữ gìn mối quan hệ và Sự thấu cảm cảm xúc",
        "Giải mã phản xạ tâm lý đối lập giữa hai kiểu tính cách"
    ],
    "📱 Công nghệ & Thiết bị Điện tử": [
        "So sánh về Kho ứng dụng, Hệ sinh thái & Độ mượt mà lâu dài",
        "So sánh về Bảo mật dữ liệu, Quyền riêng tư & An toàn thông tin",
        "So sánh về Độ bền thân máy, Khả năng chống va đập & Chống nước",
        "So sánh về Camera quay phim đêm & Chụp ảnh chân dung thực tế",
        "So sánh về Thời lượng Pin, Tốc độ Sạc nhanh & Quản lý nhiệt độ"
    ],
    "🤖 Phần Mềm, Ứng Dụng & Công Cụ AI": [
        "So sánh về Khả năng viết code lập trình & Giải quyết logic phức tạp",
        "So sánh về Văn phong viết tiếng Việt & Độ tự nhiên trong giao tiếp",
        "So sánh về Tốc độ phản hồi & Tính ổn định khi xử lý dữ liệu lớn"
    ],
    "💻 Tương Lai Việc Làm: AI vs Kỹ Năng Con Người": [
        "So sánh về Tốc độ hoàn thành công việc và Chi phí vận hành",
        "So sánh về Khả năng sáng tạo cảm xúc và Độ thấu hiểu con người",
        "Xu hướng thị trường lao động và Kỹ năng cốt lõi không thể thay thế"
    ],
    "🚗 Xe cộ & Phương tiện Di chuyển": [
        "So sánh về Chi phí vận hành, Tiết kiệm tiền nhiên liệu mỗi tháng",
        "So sánh về Độ bền bỉ động cơ, Chi phí bảo dưỡng & Thay thế linh kiện",
        "So sánh về Cảm giác lái, Độ êm ái khi đi đường dài & Tiện ích thông minh"
    ],
    "🎮 Game & Thiết Bị Giải Trí": [
        "So sánh về Kho game độc quyền & Trải nghiệm đồ họa đỉnh cao",
        "So sánh về Độ tiện lợi, Khả năng chơi mọi lúc mọi nơi & Giá game"
    ],
    "👨‍👩‍👧 Tranh Luận Nuôi Dạy Con & Gia Đình": [
        "So sánh về Sự tự lập bản lĩnh và Khả năng thích nghi xã hội của con",
        "So sánh về Sự gắn kết tình cảm gia đình và Tâm lý phát triển lành mạnh",
        "Góc nhìn giáo dục hiện đại đối lập với phương pháp truyền thống"
    ],
    "🐾 Thú Cưng: Nuôi Dạy & So Sánh Giống Loài": [
        "So sánh về Chi phí nuôi nấng, Chăm sóc sức khỏe & Thức ăn",
        "So sánh về Tính cách, Độ quấn chủ & Mức độ dễ huấn luyện"
    ],
    "🐕 Giải Mã Hành Vi Thú Cưng & Bí Ẩn Động Vật": [
        "Giải mã tín hiệu giao tiếp thực sự so với ngộ nhận của con người",
        "So sánh về Bản năng sinh tồn tự nhiên và Môi trường nuôi nhốt",
        "Sự thật khoa học động vật học gây bất ngờ nhất"
    ],
    "🌍 Nghịch Lý Địa Lý & Văn Hóa Thế Giới": [
        "So sánh về Sự tương phản văn hóa và Tập quán đời sống thú vị",
        "Bóc trần sự thật địa lý trái ngược với tưởng tượng thông thường",
        "Góc nhìn đa chiều về lối sống và tư duy các nền văn minh"
    ],
    "📜 Bí Ẩn Lịch Sử & Lầm Tưởng Cổ Nhân": [
        "So sánh về Bằng chứng khảo cổ học thực tế và Lời đồn phim ảnh",
        "Bóc trần sự thật công nghệ cổ đại và Trí tuệ của tiền nhân",
        "Góc nhìn lịch sử khách quan trung lập dựa trên dữ liệu"
    ]
}

DEFAULT_ANGLES = [
    "So sánh về Hiệu năng thực tế và Độ mượt mà lâu dài",
    "So sánh về Tính thực dụng, Giá tiền và Độ đáng mua",
    "So sánh về Độ bền, Thiết kế đẳng cấp và Trải nghiệm hằng ngày",
    "Góc nhìn tranh luận nảy lửa, so sánh đối lập sâu sắc",
    "Trải nghiệm thực tế sau thời gian dài sử dụng"
]

MODELS_PRIORITY = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.6-flash"
]

import content_moderator

SYSTEM_PROMPT_SINGLE = """
Bạn là chuyên gia biên kịch video ngắn viral (TikTok, YouTube Shorts, Reels) hàng đầu Việt Nam.
Nhiệm vụ của bạn là nhận một chủ đề so sánh giữa 2 sản phẩm/đối tượng theo một KHÍA CẠNH CỤ THỂ và xuất ra một kịch bản so sánh chi tiết, hấp dẫn.

🛡️ QUY TẮC CỐ ĐỊNH VỀ PHÁP LÝ & TIÊU CHUẨN CỘNG ĐỒNG (BẮT BUỘC TUÂN THỦ 100%):
1. TUÂN THỦ PHÁP LUẬT VIỆT NAM:
   - Tuyệt đối KHÔNG nhắc đến chính trị, tôn giáo, phân biệt vùng miền, mê tín dị đoan.
   - Tuyệt đối KHÔNG quảng bá, cổ xúy cờ bạc, cá độ, tài xỉu, lô đề, chất cấm, ma túy, thuốc lá điện tử, vũ khí, bạo lực.
   - Tuyệt đối KHÔNG vu khống, bôi nhọ danh dự tổ chức/cá nhân, không tung tin sai sự thật hoặc hàng giả, hàng cấm.
2. TUÂN THỦ CHÍNH SÁCH NỀN TẢNG (TIKTOK, YOUTUBE SHORTS, FACEBOOK REELS):
   - Tuyệt đối KHÔNG ngôn từ thù ghét (Hate speech), quấy rối, chửi bậy, thô tục, nội dung 18+ khiêu dâm.
   - So sánh dựa trên sự thật khách quan, thông số kỹ thuật, trải nghiệm thực tế và văn hóa ẩm thực/đời sống lành mạnh.
3. VĂN PHONG VĂN MINH, HÀI HƯỚC, TÍCH CỰC:
   - Giọng điệu tôn trọng cả 2 bên so sánh, kích thích thảo luận văn minh, tôn vinh giá trị thực tế của mỗi đối tượng.

QUY ĐỊNH THỜI LƯỢNG & NỘI DUNG BẮT BUỘC (35 GIÂY - 50 GIÂY):
- Kịch bản PHẢI có đúng từ 5 đến 6 phân đoạn (segments) mạch lạc, có dẫn chứng, phân tích sâu, giọng điệu tự nhiên, kích thích tranh luận cao.
- Độ dài tổng thể khi đọc voiceover phải đạt khoảng 35 - 50 giây (tổng khoảng 90 - 130 từ tiếng Việt chuẩn).

CẤU TRÚC JSON ĐẦU RA BẮT BUỘC:
{
  "title": "Tiêu đề ngắn cực giật gân (dưới 8 từ, viết HOA/Thường có dấu chuẩn)",
  "category": "Tên thể loại",
  "angle": "Khía cạnh so sánh cụ thể",
  "item_a": {
    "name": "Tên ngắn gọn đối tượng A",
    "search_query": "Từ khóa tìm ảnh sản phẩm A chất lượng cao trên nền trắng"
  },
  "item_b": {
    "name": "Tên ngắn gọn đối tượng B",
    "search_query": "Từ khóa tìm ảnh sản phẩm B chất lượng cao trên nền trắng"
  },
  "segments": [
    {
      "segment_id": 1,
      "pose": "pointing",
      "voiceover_text": "Câu mở đầu (Hook) gây tò mò, nêu rõ khía cạnh so sánh giữa A và B.",
      "highlight_item": "both",
      "sfx": "whoosh"
    },
    {
      "segment_id": 2,
      "pose": "thinking",
      "voiceover_text": "Phân tích điểm mạnh nổi trội của A ở khía cạnh này kèm dẫn chứng thực tế.",
      "highlight_item": "A",
      "sfx": "pop"
    },
    {
      "segment_id": 3,
      "pose": "thinking",
      "voiceover_text": "Phân tích điểm đối trọng của B hoặc ưu thế vượt trội của B.",
      "highlight_item": "B",
      "sfx": "pop"
    },
    {
      "segment_id": 4,
      "pose": "chill",
      "voiceover_text": "Đánh giá chi tiết, so sánh trực diện kết quả giữa 2 bên.",
      "highlight_item": "both",
      "sfx": "whoosh"
    },
    {
      "segment_id": 5,
      "pose": "chill",
      "voiceover_text": "Lời khuyên thực tế: Ai nên chọn A và ai nên chọn B.",
      "highlight_item": "both",
      "sfx": "pop"
    },
    {
      "segment_id": 6,
      "pose": "cta",
      "voiceover_text": "Câu chốt kêu gọi bình luận (Ví dụ: Vậy ở khía cạnh này, bạn chọn phe nào? Hãy bình luận cho mình biết nhé!).",
      "highlight_item": "both",
      "sfx": "whoosh"
    }
  ]
}
"""

SYSTEM_PROMPT_BATCH = """
Bạn là chuyên gia biên kịch video ngắn viral (TikTok, YouTube Shorts, Reels) hàng đầu Việt Nam.
Nhiệm vụ của bạn là nhận một Thể loại / Chủ đề và xuất ra một MẺ NHIỀU KỊCH BẢN SO SÁNH KHÁC NHAU (Batch Scripts).
Mỗi kịch bản PHẢI khai thác một CẶP SẢN PHẨM hoặc KHÍA CẠNH SO SÁNH HOÀN TOÀN KHÁC BIỆT (Ví dụ cùng iPhone vs Samsung nhưng 1 kịch bản về Bảo mật, 1 kịch bản về Kho ứng dụng, 1 kịch bản về Độ bền, 1 kịch bản về Camera đêm, v.v.).

🛡️ QUY TẮC CỐ ĐỊNH VỀ PHÁP LÝ & TIÊU CHUẨN CỘNG ĐỒNG (BẮT BUỘC TUÂN THỦ 100%):
1. TUÂN THỦ PHÁP LUẬT VIỆT NAM:
   - Tuyệt đối KHÔNG nhắc đến chính trị, tôn giáo, phân biệt vùng miền, mê tín dị đoan.
   - Tuyệt đối KHÔNG quảng bá, cổ xúy cờ bạc, cá độ, tài xỉu, lô đề, chất cấm, ma túy, thuốc lá điện tử, vũ khí, bạo lực.
   - Tuyệt đối KHÔNG vu khống, bôi nhọ danh dự tổ chức/cá nhân, không tung tin sai sự thật hoặc hàng giả, hàng cấm.
2. TUÂN THỦ CHÍNH SÁCH NỀN TẢNG (TIKTOK, YOUTUBE SHORTS, FACEBOOK REELS):
   - Tuyệt đối KHÔNG ngôn từ thù ghét (Hate speech), quấy rối, chửi bậy, thô tục, nội dung 18+ khiêu dâm.
   - So sánh dựa trên sự thật khách quan, thông số kỹ thuật, trải nghiệm thực tế và văn hóa ẩm thực/đời sống lành mạnh.
3. VĂN PHONG VĂN MINH, HÀI HƯỚC, TÍCH CỰC:
   - Giọng điệu tôn trọng cả 2 bên so sánh, kích thích thảo luận văn minh, tôn vinh giá trị thực tế của mỗi đối tượng.

QUY ĐỊNH THỜI LƯỢNG (35s - 50s mỗi video):
- Mỗi kịch bản có đúng 5 đến 6 phân đoạn (segments).
- Trả về DUY NHẤT một mảng JSON các kịch bản: `[ { ...kịch bản 1... }, { ...kịch bản 2... }, ... ]`
"""

def clean_json_string(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()

def _http_gemini_call(api_key: str, model: str, prompt: str, system_instruction: str = "") -> Optional[str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.85
        }
    }
    
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                resp_json = json.loads(resp.read().decode("utf-8"))
                candidates = resp_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
    except urllib.error.HTTPError as he:
        err_body = he.read().decode("utf-8")
        raise RuntimeError(f"HTTP {he.code}: {err_body}")
    except Exception as ex:
        raise ex
        
    return None

def test_gemini_api_key(api_key: str) -> Tuple[bool, str]:
    key = api_key.strip()
    if not key:
        return False, "Vui lòng nhập API Key trước khi kiểm tra."
        
    for m in MODELS_PRIORITY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": "ping"}]}], "generationConfig": {"maxOutputTokens": 5}}
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    return True, f"Kết nối thành công! Đang sử dụng mô hình Google {m}."
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8")
            if "API_KEY_INVALID" in err_body:
                return False, "API Key không hợp lệ. Vui lòng kiểm tra lại."
            elif "RESOURCE_EXHAUSTED" in err_body or "QUOTA" in err_body:
                return False, "API Key đã vượt quá hạn mức miễn phí (Quota limit)."
            continue
        except Exception:
            continue
            
    return False, "Không thể kết nối đến máy chủ Google Gemini. Vui lòng kiểm tra lại Key."

def get_fallback_script(topic: str, category: str = "Công nghệ", angle: str = "Hiệu năng & Độ bền") -> Dict[str, Any]:
    parts = re.split(r"\s+(?:vs|và|với|hoặc)\s+", topic, flags=re.IGNORECASE)
    if len(parts) >= 2:
        name_a = parts[0].strip()
        name_b = parts[1].strip()
    else:
        name_a = topic.strip() or "Sản phẩm A"
        name_b = "Sản phẩm B"
        
    return {
        "title": f"{name_a} VS {name_b}: KÈO ĐẤU {angle.upper()[:18]}!",
        "category": category,
        "angle": angle,
        "item_a": {
            "name": name_a,
            "search_query": f"{name_a} product photo high resolution"
        },
        "item_b": {
            "name": name_b,
            "search_query": f"{name_b} product photo high resolution"
        },
        "segments": [
            {
                "segment_id": 1,
                "pose": "pointing",
                "voiceover_text": f"Nếu so sánh giữa {name_a} và {name_b} về mặt {angle}, đâu mới thực sự là lựa chọn số 1 dành cho bạn?",
                "highlight_item": "both",
                "sfx": "whoosh"
            },
            {
                "segment_id": 2,
                "pose": "thinking",
                "voiceover_text": f"Đầu tiên, xét về {name_a}, sản phẩm này gây ấn tượng mạnh với sự hoàn thiện tinh xảo và trải nghiệm thực tế vô cùng mượt mà.",
                "highlight_item": "A",
                "sfx": "pop"
            },
            {
                "segment_id": 3,
                "pose": "thinking",
                "voiceover_text": f"Tuy nhiên, {name_b} lại không hề chịu thua kém khi sở hữu những ưu thế vượt trội về tính đa dụng và hiệu năng cực kỳ ấn tượng.",
                "highlight_item": "B",
                "sfx": "pop"
            },
            {
                "segment_id": 4,
                "pose": "chill",
                "voiceover_text": f"Khi đặt cả hai lên bàn cân, sự chênh lệch sẽ thể hiện rất rõ tùy thuộc vào thói quen và nhu cầu thực tế của từng người.",
                "highlight_item": "both",
                "sfx": "whoosh"
            },
            {
                "segment_id": 5,
                "pose": "chill",
                "voiceover_text": f"Nếu bạn thích sự ổn định lâu dài hãy chọn {name_a}, còn nếu đề cao sự tiện lợi và tối ưu hãy về đội {name_b}.",
                "highlight_item": "both",
                "sfx": "pop"
            },
            {
                "segment_id": 6,
                "pose": "cta",
                "voiceover_text": "Vậy đứng ở góc nhìn này, bạn sẽ bình chọn cho ai? Hãy để lại ý kiến bên dưới phần bình luận nhé!",
                "highlight_item": "both",
                "sfx": "whoosh"
            }
        ]
    }

def generate_single_comparison_script(
    category: str,
    specific_topic: Optional[str] = None,
    used_titles: Optional[List[str]] = None,
    used_pairs: Optional[List[str]] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Generate exactly 1 fresh, highly creative, non-duplicate comparison script on-demand in ~1 second."""
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        
    if not api_key:
        raise RuntimeError("Chưa cấu hình Gemini API Key. Vui lòng bấm nút '⚙️ Cài Đặt API Key' trên giao diện để nhập key của bạn.")
        
    avoid_sections = []
    if used_pairs:
        avoid_sections.append(f"1. TUYỆT ĐỐI KHÔNG SO SÁNH LẠI CÁC CẶP ĐÃ LÀM: {json.dumps(used_pairs[-30:], ensure_ascii=False)}.")
    if used_titles:
        avoid_sections.append(f"2. TUYỆT ĐỐI KHÔNG TRÙNG TIÊU ĐỀ: {json.dumps(used_titles[-30:], ensure_ascii=False)}.")
        
    avoid_instruction = "\n".join(avoid_sections) if avoid_sections else "Hãy sáng tạo cặp đối tượng hoàn toàn mới lạ và bắt trend."
    topic_target = specific_topic if specific_topic else f"một cặp đối tượng so sánh hoàn toàn mới lạ, nổi bật, hấp dẫn trong thể loại '{category}'"
    
    prompt = f"""
Hãy tạo ĐÚNG 1 KỊCH BẢN video ngắn (35 - 50 giây, đúng 5 đến 6 segments) cho thể loại: '{category}'.
Đối tượng so sánh: {topic_target}.

QUY TẮC CHỐNG TRÙNG LẶP TUYỆT ĐỐI:
{avoid_instruction}

YÊU CẦU NỘI DUNG:
- Hãy tự do sáng tạo một cặp đối tượng độc đáo, hấp dẫn chưa từng xuất hiện.
- Phân tích sâu sắc, kịch tính, kích thích tranh luận văn minh.

Trả về DUY NHẤT một JSON Object kịch bản chuẩn xác theo cấu trúc quy định.
"""
    last_err = ""
    for m in MODELS_PRIORITY:
        try:
            raw = _http_gemini_call(api_key, m, prompt, SYSTEM_PROMPT_SINGLE)
            if raw:
                data = json.loads(clean_json_string(raw))
                if "title" in data and "segments" in data:
                    data["category"] = category
                    if specific_topic:
                        data["topic"] = specific_topic
                    is_safe, reason = content_moderator.audit_script_compliance(data)
                    if is_safe:
                        print(f"[GeminiService] Đã tạo thành công 1 kịch bản mới bằng model {m}!")
                        return data
                    else:
                        print(f"[GeminiService] Kịch bản bị từ chối do vi phạm chính sách: {reason}")
        except Exception as e:
            last_err = str(e)
            print(f"[GeminiService] Model {m} error: {e}")
            continue
            
    # Fail-Fast: Never use fake/template fallback scripts!
    raise RuntimeError(f"Lỗi kết nối Gemini AI: {last_err}. Vui lòng kiểm tra lại kết nối internet hoặc API Key.")

def generate_batch_scripts(
    category: str,
    count: int = 5,
    specific_topic: Optional[str] = None,
    used_titles: Optional[List[str]] = None,
    used_pairs: Optional[List[str]] = None,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Generate a batch of 5 deep comparison scripts dynamically with Gemini AI, ensuring ZERO duplicate pairs/titles."""
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        
    if not api_key:
        raise RuntimeError("Chưa cấu hình Gemini API Key. Vui lòng bấm nút '⚙️ Cài Đặt API Key' trên giao diện.")
        
    avoid_sections = []
    if used_pairs:
        avoid_sections.append(f"1. TUYỆT ĐỐI KHÔNG SO SÁNH LẠI CÁC CẶP ĐÃ LÀM SAU ĐÂY: {json.dumps(used_pairs[-25:], ensure_ascii=False)}.")
    if used_titles:
        avoid_sections.append(f"2. TUYỆT ĐỐI KHÔNG TRÙNG TIÊU ĐỀ: {json.dumps(used_titles[-25:], ensure_ascii=False)}.")
        
    avoid_instruction = "\n".join(avoid_sections) if avoid_sections else "Hãy sáng tạo các cặp so sánh mới lạ, độc đáo, bắt trend nhất."
    topic_target = specific_topic if specific_topic else f"các cặp đối tượng hoàn toàn mới lạ, nổi bật, hấp dẫn trong thể loại '{category}'"
    
    prompt = f"""
Hãy tạo ĐÚNG {count} kịch bản video ngắn (mỗi video dài 35 - 50 giây, đúng 5-6 segments) cho thể loại: '{category}'.
Đối tượng so sánh: {topic_target}.

QUY TẮC CHỐNG TRÙNG LẶP & ĐA DẠNG HÓA SÁNG TẠO:
{avoid_instruction}

YÊU CẦU NỘI DUNG:
- Mỗi kịch bản PHẢI là một CẶP ĐỐI TƯỢNG HOÀN TOÀN MỚI LẠ HOẶC KHÍA CẠNH SO SÁNH ĐẶC SẮC KHÁC NHAU.
- Ví dụ nếu là Ẩm thực: hãy sáng tạo các cặp như (Cơm sườn vs Cơm gà, Trà tắc vs Trà đào, Bún mắm vs Bún riêu, Bánh bao vs Bánh chưng, v.v.).
- Nếu là Thú cưng: hãy sáng tạo (Husky vs Alaska, Mèo Ba Tư vs Mèo Sphynx, Chuột Hamster vs Sóc Bay, v.v.).
- Nếu là Xe cộ: hãy sáng tạo (VinFast VF3 vs Wuling Mini EV, Winner X vs Exciter 155, v.v.).

Trả về DUY NHẤT một mảng JSON hợp lệ chứa đúng {count} object kịch bản.
"""
    last_err = ""
    for m in MODELS_PRIORITY:
        try:
            raw = _http_gemini_call(api_key, m, prompt, SYSTEM_PROMPT_BATCH)
            if raw:
                data = json.loads(clean_json_string(raw))
                if isinstance(data, list) and len(data) > 0:
                    safe_scripts = []
                    for s in data:
                        s["category"] = category
                        if specific_topic:
                            s["topic"] = specific_topic
                        is_safe, reason = content_moderator.audit_script_compliance(s)
                        if is_safe:
                            safe_scripts.append(s)
                        else:
                            print(f"[GeminiService] Đã loại bỏ kịch bản không đạt chuẩn an toàn: {reason}")
                    if safe_scripts:
                        print(f"[GeminiService] Đã tạo thành công {len(safe_scripts)} kịch bản mới lạ bằng model {m}!")
                        return safe_scripts
        except Exception as e:
            last_err = str(e)
            print(f"[GeminiService] Batch error with {m}: {e}")
            continue
            
    raise RuntimeError(f"Lỗi kết nối Gemini AI: {last_err}. Vui lòng kiểm tra lại kết nối internet hoặc API Key.")

def generate_seo_metadata(script_data: Dict[str, Any], category: str = "") -> str:
    """Tự động tạo nội dung mô tả bài viết chuẩn SEO (Hook + Description + CTA + Niche Hashtags)."""
    title = script_data.get("title", "Kịch bản so sánh đỉnh cao")
    item_a = script_data.get("item_a", {}).get("name", "Bên A")
    item_b = script_data.get("item_b", {}).get("name", "Bên B")
    angle = script_data.get("angle", "Góc nhìn thực tế")
    
    clean_cat = re.sub(r'[^\w\s]', '', category).lower().strip().replace(" ", "") if category else "sosanh"
    tag_a = re.sub(r'[^\w\s]', '', item_a).lower().strip().replace(" ", "")
    tag_b = re.sub(r'[^\w\s]', '', item_b).lower().strip().replace(" ", "")
    
    hook = f"🔥 {title} — Liệu {item_a} hay {item_b} mới là sự lựa chọn số 1?"
    desc = f"Phân tích chuyên sâu và so sánh chi tiết giữa {item_a} và {item_b} về mặt {angle.lower()}. Đánh giá khách quan ưu nhược điểm để giúp bạn đưa ra quyết định chuẩn xác nhất."
    cta = f"👉 Bạn theo phe của {item_a} hay {item_b}? Hãy để lại bình luận và quan điểm của bạn ngay bên dưới nhé! 👇"
    tags = f"#reels #shorts #sosanh #{clean_cat} #{tag_a} #{tag_b} #review #trending #viral #xuhuong #fyp"
    
    return f"{hook}\n\n{desc}\n\n{cta}\n\n{tags}"

if __name__ == "__main__":
    print("Testing 35s-50s script generation & Batch engine...")