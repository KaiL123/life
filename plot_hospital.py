import pandas as pd
import requests
import json
import warnings
import numpy as np
import folium
warnings.filterwarnings('ignore')

# 根据地址获取经纬度
def address2lng(address, url, ak):
    html = requests.get(url.format(address=address, ak=ak))
    response = html.text
    response = json.loads(response.split('(')[1][:-1])
    if response['status'] == 0:
        lng = response['result']['location']['lng']
        lat = response['result']['location']['lat']
        return lng, lat
    else:
        return 0

def etl(path, ak):
	data = pd.read_excel(path)
	df = data[['连锁企业', '行政区域', '门店地址']]
	url = 'http://api.map.baidu.com/geocoding/v3/?address={address}&output=json&ak={ak}&callback=showLocation'
	df['flag1'] = df.apply(lambda x: x['行政区域'][:2]==x['门店地址'][:2], axis=1)
	df['address'] = df.apply(lambda x: '上海'+x['门店地址'] if x['flag1'] else '上海'+x['行政区域']+'区'+x['门店地址'], axis=1)
	df['num'] = df['address'].apply(lambda x: address2lng(x, url, ak))
	df['num'] = df['num'].astype('str')
	# df.loc[df['num']=='0', 'num'] = '(121.564059, 31.232979)'
	# 删除没有搜索到经纬度的地方
	df = df[df['num'] != '0']
	df_grid = df['num'].str.split(", ", expand=True)
	df_grid.columns = ['lng', 'lat']
	df_grid['lng'] = df_grid['lng'].astype(str)
	df_grid['lat'] = df_grid['lat'].astype(str)
	df_grid['lng'] = df_grid['lng'].apply(lambda x: x[1:])
	df_grid['lat'] = df_grid['lat'].apply(lambda x: x[:-1])
	df_grid['lng'] = df_grid['lng'].astype(float)
	df_grid['lat'] = df_grid['lat'].astype(float)
	df = pd.concat([df, df_grid], axis=1)
	df = df[['门店地址', 'lng', 'lat']]
	df.to_csv('grid.csv', index=False)
	return df

# 画图，这是所有点的图，在加上自己的额外添加的坐标点
def plot_whole(your_address, df):
	china_address = your_address
	your = address2lng(china_address, url)

	m = folium.Map(location=[35,110],zoom_start=2)    #绘制Map，开始缩放程度是5倍
	for address, lng, lat in zip(df['门店地址'], df['lng'], df['lat']):
	    folium.Marker([lat, lng], popup='<i>%s</i>' % (address)).add_to(m)
	folium.Marker([your[1], your[0]], popup='<i>%s</i>' % (your_address), icon=folium.Icon(color='green')).add_to(m)
	m.save('whole_hospital.html')

# 取经纬度在[x-0.05, x+0.05]范围内的坐标点
def plot_near(your_address, df):
	china_address = your_address
	your = address2lng(china_address, url)
	df['help'] = df['lng'].apply(lambda x: (your[0] - 0.05) <= x <= (your[0] + 0.05))
	df = df[df['help']]
	df['help'] = df['lat'].apply(lambda x: (your[1] - 0.05) <= x <= (your[1] + 0.05))
	df = df[df['help']]

	m = folium.Map(location=[35,110],zoom_start=2)    #绘制Map，开始缩放程度是5倍
	for address, lng, lat in zip(df['门店地址'], df['lng'], df['lat']):
	    folium.Marker([lat, lng], popup='<i>%s</i>' % (address)).add_to(m)
	folium.Marker([your[1], your[0]], popup='<i>%s</i>' % (your_address), icon=folium.Icon(color='green')).add_to(m)
	m.save('near_hospital.html')

if __name__ == '__main__':
	# ak为百度地图开发者项目创建后的key
	ak = 'UG0yUO3cYe5PVsOc4TfbYGXEFIHafCXD'
	path = '1000个网点-分区优化.xlsx'
	your_address = input('Please input your address: ')
	df = etl(path, ak)
	plot_near(your_address, df)
	# plot_whole(your_address, df)