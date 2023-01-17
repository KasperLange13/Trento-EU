import json
import math

import pandas as pd


def create_csv():
    with open('POI.json') as f:
        data = json.load(f)
        series = []
        for element in data:
            poiData = element['content']['poiData']
            objData = element['content']['objData']
            location = poiData['location']
            address = location['addresses']['IT']
            clean_element = {'id': element['domainId'],
                             'name': objData['name']['IT'],
                             'description': objData['description']['IT'],
                             'longitude': location['coordinate']['longitude'],
                             'latitude': location['coordinate']['latitude'],
                             'srsSystem': location['coordinate']['srsName'],
                             'topics': objData['topics'],
                             'street': address['street'],
                             'city': address['city'],
                             'postal_code': address['postalCode'],
                             'region': address['region'],
                             'category': objData['category']}
            if 'IT' in poiData['timetable']:
                clean_element['timetable'] = poiData['timetable']['IT']
            else:
                clean_element['timetable'] = ''

            if 'IT' in objData['serviceDescription']:
                clean_element['service'] = objData['serviceDescription']['IT']
            else:
                clean_element['service'] = ''
            series.append(pd.Series(data=clean_element, index=clean_element.keys()))
        df = pd.concat(series, ignore_index=True, axis=1)
        df = df.transpose()
    df.to_csv('POI.csv', index=False)


def clean_csv():
    df = pd.read_csv('POI.csv')
    categories = ['prodottitipici', 'attrazionenaturale', 'agriturismo', 'monumento', 'museo',
                  'ufficioinformazionituristiche', 'rifugio', 'sitoarcheologico', 'Prodottoenogatronomico',
                  'Prodottodiartigianatolocale', 'Caseificio', 'infoturistiche/ufficioturistico', 'teatro/opera/cinema',
                  'Rifugio/Malga', 'Attrazionenaturale']
    cleaned_df = df.loc[df.category.isin(categories)]
    cleaned_df.to_csv('POI_clean.csv', index=False)


def extract_coords_POI():
    df = pd.read_csv('POI_clean.csv')
    df_coordinates = df[['longitude', 'latitude', 'srsSystem']].copy()
    df_coordinates.reset_index(inplace=True)
    df_coordinates['coordinates_id'] = df_coordinates.apply(lambda x: 'POI' + str(x['index']), axis=1)
    df_coordinates.pop('index')
    df = pd.merge(df, df_coordinates, how='left', on=['longitude', 'latitude', 'srsSystem'])
    df = df.drop(['longitude', 'latitude', 'srsSystem'], axis=1)
    df.to_csv('POI_clean.csv', index=False)
    df_coordinates.to_csv('POI_coordinates.csv', index=False)


def clean_topic_str(topic):
    topic = topic.replace("[", "")
    topic = topic.replace("]", "")
    topic = topic.replace("'", "")
    topic = topic.replace(" ", "")
    topic = topic.lower()
    return topic


def create_topic_df():
    df = pd.read_csv('POI_clean.csv')
    topics_list = []
    for topic in list(df.topics.unique()):
        topic = clean_topic_str(topic)
        if topic != '':
            topics_list.append(topic.split(','))

    topics_list = [topic for sub_list in topics_list for topic in sub_list]
    topics_set = set(topics_list)
    df_topics = pd.DataFrame(topics_set, columns=['name'])
    df_topics.reset_index(inplace=True)
    df_topics.rename(columns={'index': 'topic_id'}, inplace=True)
    df_topics.to_csv('POI_topics.csv', index=False)


def create_POI_topic_relation_df():
    df = pd.read_csv('POI_clean.csv')
    df_topics = pd.read_csv('POI_topics.csv')
    POI_topics = []
    for idx in df.index:
        entity = df.iloc[idx]
        entity_topics = clean_topic_str(entity.topics)
        topic_list = entity_topics.split(',')
        for topic in topic_list:
            if topic != '':
                topic_id = df_topics.loc[df_topics['name'] == topic]['topic_id'].values[0]
                POI_topics.append([entity.id, topic_id])
    df_POI_topics = pd.DataFrame(POI_topics, columns=['POI_id', 'topic_id'])
    df_POI_topics.to_csv('POI_topics_relation.csv', index=False)
    df = df.drop('topics', axis=1)
    df.to_csv('POI_clean.csv', index=False)


def create_region_csv():
    df = pd.read_csv('POI_clean.csv')
    region_list = list(df.region.unique())

    df_region = pd.DataFrame(region_list, columns=['code'])
    df_region.reset_index(inplace=True)
    df_region.rename(columns={'index': 'region_id'}, inplace=True)
    df_region.to_csv('POI_regions.csv', index=False)
    df['region_id'] = df.apply(lambda x: df_region.loc[df_region['code'] == x.region].region_id[0], axis=1)
    df = df.drop('region', axis=1)
    df.to_csv('POI_clean.csv', index=False)


def create_city_csv():
    df = pd.read_csv('POI_clean.csv')
    df_cities = df[['city', 'postal_code', 'region_id']].copy()
    df_cities.reset_index(inplace=True)
    df_cities.rename(columns={'index': 'city_id'}, inplace=True)
    df_cities['city_id'] = df_cities.city_id.astype('str')
    df_cities.drop_duplicates(keep='first', subset=['postal_code'], inplace=True)
    df = pd.merge(df, df_cities, how='left', on=['city', 'postal_code', 'region_id'])
    df = df.drop(['city', 'postal_code', 'region_id'], axis=1)
    df.to_csv('POI_clean.csv', index=False)
    df_cities.to_csv('POI_cities.csv', index=False)


def create_street_csv():
    df = pd.read_csv('POI_clean.csv', dtype='str')
    df_streets = df[['street', 'city_id']].copy()
    df_streets.reset_index(inplace=True)
    df_streets.rename(columns={'index': 'street_id'}, inplace=True)
    df_streets.drop_duplicates(keep='first', subset=['street', 'city_id'], inplace=True)
    df = pd.merge(df, df_streets, how='left', on=['street', 'city_id'])
    df = df.drop(['street', 'city_id'], axis=1)
    df.to_csv('POI_clean.csv', index=False)
    df_streets.to_csv('POI_streets.csv', index=False)


def all_process():
    create_csv()
    clean_csv()
    extract_coords_POI()
    create_topic_df()
    create_POI_topic_relation_df()
    create_region_csv()
    create_city_csv()
    create_street_csv()


def extract_coords_stops():
    df = pd.read_csv('GTFS/stops.txt',  dtype='str')
    df_coordinates = df[['stop_lat', 'stop_lon']].copy()
    df_coordinates.reset_index(inplace=True)
    df_coordinates['coordinates_id'] = df_coordinates.apply(lambda x: 'STOP' + str(x['index']), axis=1)
    df_coordinates.pop('index')
    df = pd.merge(df, df_coordinates, how='left', on=['stop_lat', 'stop_lon'])
    df = df.drop(['stop_lat', 'stop_lon'], axis=1)
    df.to_csv('GTFS/stops_clean.csv', index=False)
    df_coordinates.to_csv('GTFS/Stops_coordinates.csv', index=False)


def calculate_distance(lat_1, lng_1, lat_2, lng_2):
    lng_1, lat_1, lng_2, lat_2 = map(float, [lng_1, lat_1, lng_2, lat_2])
    lng_1, lat_1, lng_2, lat_2 = map(math.radians, [lng_1, lat_1, lng_2, lat_2])

    d_lat = lat_2 - lat_1
    d_lng = lng_2 - lng_1

    temp = (
            math.sin(d_lat / 2) ** 2
            + math.cos(lat_1)
            * math.cos(lat_2)
            * math.sin(d_lng / 2) ** 2
    )

    return 6373.0 * (2 * math.atan2(math.sqrt(temp), math.sqrt(1 - temp)))


def check_distance(lat_1, lng_1, lat_2, lng_2):
    lng_1, lat_1, lng_2, lat_2 = map(float, [lng_1, lat_1, lng_2, lat_2])
    distance = calculate_distance(lat_1, lng_1, lat_2, lng_2)
    return distance <= 0.5


def close_coords():
    df_stops_coordinates = pd.read_csv('GTFS/Stops_coordinates.csv', dtype='str')
    df_POI_coordinates = pd.read_csv('POI_coordinates.csv', dtype='str')
    df_coordinates = pd.merge(df_stops_coordinates, df_POI_coordinates, how='cross', suffixes=['_stops', '_POI'])
    df_coordinates['close'] = df_coordinates.apply(lambda x: check_distance(x.stop_lat, x.stop_lon, x.latitude, x.longitude), axis=1)
    df_coordinates = df_coordinates[df_coordinates.close]
    df_coordinates = df_coordinates.drop(['stop_lat', 'stop_lon', 'longitude', 'latitude', 'srsSystem'], axis=1)
    df_coordinates.to_csv('GTFS/close_POI_stop.csv', index=False)
