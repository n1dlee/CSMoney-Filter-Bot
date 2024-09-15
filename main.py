from fake_useragent import UserAgent
import requests
import json
from urllib.parse import quote

ua = UserAgent()

def collect_data(weapon_types, min_price=10, max_price=100, qualities=None, stattrak=None, offset=0, batch_size=5):
    url = f'https://cs.money/1.0/market/sell-orders?limit={batch_size}&offset={offset}&minPrice={min_price}&maxPrice={max_price}&type=2'
    
    for weapon in weapon_types:
        url += f'&weapon={quote(weapon)}'
    
    if qualities:
        for quality in qualities:
            url += f'&quality={quality.lower()}'
    
    if stattrak:
        url += '&isStatTrak=true'
    
    response = requests.get(url=url, headers={'user-agent': f'{ua.random}'})

    data = response.json()
    items = data.get('items', [])

    result = []
    for item in items:
        asset = item.get('asset', {})
        pricing = item.get('pricing', {})
        
        item_full_name = asset.get('names', {}).get('full')
        item_3d = item.get('links', {}).get('3d')
        item_price = pricing.get('default')
        item_discount = pricing.get('discount')
        item_float = asset.get('float')

        result.append({
            'full': item_full_name,
            'default': item_price,
            'discount': item_discount,
            'float': item_float,
            'links': {
                '3d': item_3d
            },
            'asset': {
                'images': {
                    'screenshot': asset.get('images', {}).get('screenshot')
                }
            }
        })

    return result

def main():
    data = collect_data(
        weapon_types=['Butterfly', 'Karambit'],
        min_price=1000,
        max_price=5000,
        qualities=['fn', 'mw', 'ft', 'ww', 'bs'], 
        stattrak=True
    )
    with open('result.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    print(f"Total items collected: {len(data)}")

if __name__ == "__main__":
    main()
