import http from 'k6/http';
import { check, sleep } from 'k6';

// --- 1. CẤU HÌNH TEST (1000 USERS) ---
export const options = {
    stages: [
        { duration: '2m', target: 500 },   // Tăng từ 0 lên 500 user
        { duration: '3m', target: 1000 },  // Tăng lên 1000 user
        { duration: '1m', target: 0 },     // Giảm về 0
    ],
    thresholds: {
        http_req_duration: ['p(95)<3000'],  // 95% request dưới 3s
        http_req_failed: ['rate<0.05'],     // Lỗi dưới 5%
    },
};

// --- 2. HÀM SETUP: ĐĂNG NHẬP 1 LẦN ĐỂ LẤY TOKEN ---
export function setup() {
    const BASE_URL = 'http://app-alb-1319109007.us-east-1.elb.amazonaws.com';
    
    // 👇👇👇 THAY BẰNG TÀI KHOẢN THẬT 👇👇👇
    const credentials = {
        email: 'minhphucpham53@gmail.com',     // THAY EMAIL
        password: 'hi123'       // THAY PASSWORD
    };
    
    // Gọi API login (cần xác định đúng endpoint)
    // Thử các endpoint phổ biến nếu chưa biết chính xác
    const loginEndpoints = [
        '/api/auth/login',
        '/api/login', 
        '/auth/login',
        '/api/v1/auth/login'
    ];
    
    let token = null;
    
    for (let endpoint of loginEndpoints) {
        let res = http.post(`${BASE_URL}${endpoint}`, JSON.stringify(credentials), {
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (res.status === 200) {
            try {
                let body = JSON.parse(res.body);
                token = body.token || body.access_token || body.data?.token;
                if (token) {
                    console.log(`✅ Login thành công tại ${endpoint}`);
                    break;
                }
            } catch(e) {}
        }
    }
    
    if (!token) {
        console.error('❌ Không thể lấy token. Kiểm tra lại endpoint login và thông tin đăng nhập!');
        return null;
    }
    
    return { token };
}

// --- 3. HÀM DEFAULT: 1000 USER DÙNG CHUNG TOKEN ĐỂ GỌI API ---
export default function(data) {
    // Kiểm tra token từ setup
    if (!data || !data.token) {
        console.error('❌ Không có token, dừng test');
        return;
    }
    
    const BASE_URL = 'http://app-alb-1319109007.us-east-1.elb.amazonaws.com';
    const TOKEN = data.token;
    
    const headers = {
        'Authorization': `Bearer ${TOKEN}`,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    };
    
    // Gọi API certificates
    let response = http.get(`${BASE_URL}/api/certificates/`, { headers });
    
    // Kiểm tra kết quả
    const success = check(response, {
        '✅ API certificates trả về 200': (r) => r.status === 200,
        '✅ Response có dữ liệu': (r) => r.body && r.body.length > 0,
    });
    
    if (!success && response.status === 401) {
        console.log(`⚠️ User ${__VU}: Token hết hạn hoặc không hợp lệ (401)`);
    } else if (response.status !== 200) {
        console.log(`❌ User ${__VU}: Lỗi ${response.status} - ${response.body.substring(0, 100)}`);
    }
    
    // Nghỉ 1 giây giữa các request
    sleep(1);
}