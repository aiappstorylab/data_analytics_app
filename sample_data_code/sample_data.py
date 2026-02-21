import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# 1. 설정 데이터
num_records = 3000
start_date = datetime(2026, 3, 1)
locations = ['Gangnam', 'Sinsa', 'Mapo', 'Hongdae', 'Yeouido']
payment_methods = ['Credit Card', 'Mobile Pay', 'Cash', 'Points']
# 연령대 정의 및 가중치 (2030 세대가 편의점 이용 빈도가 높음)
age_groups = ['10s', '20s', '30s', '40s', '50s', '60s+']
age_weights = [15, 30, 25, 15, 10, 5] 

# 카테고리별 상품 및 가격 설정
products = {
    'Fresh Food': {'참치마요 삼각김밥': 1200, '혜자로운 도시락': 5200, '샌드위치': 2800},
    'Beverage': {'아이스 아메리카노': 2500, '바나나우유': 1700, '에너지드링크': 2200},
    'Instant Food': {'불닭볶음면 큰컵': 1800, '신라면 소컵': 1100, '컵누들': 1800},
    'Snack': {'포카칩': 1700, '빼빼로': 1500, '초코빈': 1200},
    'Alcohol': {'캔맥주 500ml': 2800, '소주': 2100, '와인': 15000},
    'Tobacco': {'에쎄 프라임': 4500, '메비우스': 4500}
}

# 2. 데이터 생성 로직
data = []
categories = list(products.keys())

for i in range(num_records):
    # 랜덤 날짜 및 시간 생성
    current_date = start_date + timedelta(days=random.randint(0, 45), 
                                          hours=random.randint(0, 23),
                                          minutes=random.randint(0, 59))
    
    # 연령대 결정
    age_group = random.choices(age_groups, weights=age_weights)[0]
    
    # 연령대에 따른 선호 카테고리 가중치 조정
    if age_group == '10s':
        cat_weights = [30, 20, 30, 20, 0, 0] # 주류/담배 제외, 간식/라면 위주
    elif age_group in ['20s', '30s']:
        cat_weights = [25, 25, 15, 10, 15, 10] # 고른 분포, 간편식 선호
    elif age_group in ['40s', '50s']:
        cat_weights = [15, 15, 10, 10, 30, 20] # 주류/담배 비중 높음
    else: # 60s+
        cat_weights = [20, 20, 10, 10, 20, 20]
        
    cat = random.choices(categories, weights=cat_weights)[0]
    p_name = random.choice(list(products[cat].keys()))
    price = products[cat][p_name]
    qty = random.randint(1, 3)
    
    data.append([
        f"T{i+1:05d}",
        current_date.strftime('%Y-%m-%d'),
        current_date.strftime('%H:%M'),
        age_group, # 연령대 추가
        cat, p_name, price, qty,
        random.choice(payment_methods),
        random.choice(locations)
    ])

# 3. 데이터프레임 생성 및 저장
df = pd.DataFrame(data, columns=['Transaction_ID', 'Date', 'Time', 'Age_Group',
                                 'Category', 'Product_Name', 'Price', 'Quantity', 
                                 'Payment_Method', 'Store_Location'])

df['Total_Amount'] = df['Price'] * df['Quantity']
df.to_csv('cvs_sales_with_age.csv', index=False, encoding='utf-8-sig')
print("연령대가 포함된 데이터 생성 완료!")