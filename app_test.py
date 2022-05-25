import pytest
import json
import urllib.request
from unittest.mock import mock_open, patch
from app import *

@pytest.fixture
def mock_single_entry_one():
    """mock entry with some incomplete values"""
    single_entry = {"api_endpoint": "https://data.seattle.gov/resource/3th6-ticf.json",
                    "metric_name": "total GHG emissions in tonnes",
                    "city": "Seattle",
                    "metric_parse_code": "sum(float(d['totalghgemissions']) for d in data)",
                    "date_parse_code": "",
                    "cov_dimension_id": "",
                    "cov_metric_name": ""}
    return single_entry

@pytest.fixture
def mock_single_entry_two():
    """mock entry with complete values"""
    single_entry = {"api_endpoint": "https://data.seattle.gov/resource/3th6-ticf.json?$limit=9999999",
                    "metric_name": "% reduction in building energy emissions",
                    "city": "Seattle",
                    "metric_parse_code": "sum(float(i['totalghgemissions'])for i in data if i['epapropertytype'] == 'K-12 School')",
                    "date_parse_code": "2020",
                    "cov_dimension_id": "3054",
                    "cov_metric_name": "% reduction of total tonnes of greenhouse gas emmissions from City-owned buildings (since 2007)"
    }
    return single_entry

@pytest.fixture
def mock_invalid_api():
    """entry with invalid api endpoint"""
    single_entry = {"api_endpoint": "I am not valid"}
    return single_entry

@patch('builtins.open', mock_open(read_data='[{"metric_name": "total GHG emissions tonnes","city": "Seattle"}, {"metric_name": "greenhouse gas emissions over time" ,"city": "Calgary"}]'))
def test_get_data_from_records():
    """010A records data is stores as a list of dictionaries"""
    print(get_data_from_records())
    assert get_data_from_records() == [{'metric_name': "total GHG emissions tonnes", 'city': "Seattle"}, 
                {'metric_name': "greenhouse gas emissions over time", 'city': "Calgary"}]

@patch('builtins.open', mock_open(read_data='[{"metric_name": "total GHG emissions tonnes","city": "Seattle"}, {"metric_name": "greenhouse gas emissions over time" ,"city": "Calgary"}]'))
def test_data_type():
    """010B check data types and length of result received from get_data_from_records"""
    final_list = get_data_from_records()
    assert type(final_list) == list 
    assert type(final_list[0]) == dict
    assert len(final_list) == 2

def test_output_get_data_from_single_entry_one(mock_single_entry_one):
    """020A tests output from an incomplete entry"""
    url = mock_single_entry_one["api_endpoint"]
    with urllib.request.urlopen(mock_single_entry_one["api_endpoint"]) as url:
        data = json.loads(url.read().decode())
    assert get_data_from_single_entry(mock_single_entry_one) ==  {'Serial No.': "",
                'Metric Name': "total GHG emissions in tonnes",
                'City': "Seattle",
                'Metric Value': sum(float(d['totalghgemissions']) for d in data),
                'Date': "-",
                'CoV Dimension ID': "-",
                'CoV Metric Name': "-",
                'API Endpoint': "https://data.seattle.gov/resource/3th6-ticf.json"
                }
def test_output_get_data_from_single_entry_two(mock_single_entry_two):
    """020B tests output from a complete entry"""
    url = mock_single_entry_two["api_endpoint"]
    with urllib.request.urlopen(mock_single_entry_two["api_endpoint"]) as url:
        data = json.loads(url.read().decode())
    assert get_data_from_single_entry(mock_single_entry_two) ==  {'Serial No.': "",
                'Metric Name': "% reduction in building energy emissions",
                'City': "Seattle",
                'Metric Value': sum(float(i['totalghgemissions'])for i in data if i['epapropertytype'] == 'K-12 School'),
                'Date': "2020",
                'CoV Dimension ID': "3054",
                'CoV Metric Name': "% reduction of total tonnes of greenhouse gas emmissions from City-owned buildings (since 2007)",
                'API Endpoint': "https://data.seattle.gov/resource/3th6-ticf.json?$limit=9999999"
                }

def test_stdout_invalid_api(mock_invalid_api, capfd):
    """020C invalid api"""
    get_data_from_single_entry(mock_invalid_api)
    out, err = capfd.readouterr()
    assert out == f'API Endpoint Error: {err} {mock_invalid_api["api_endpoint"]}\n'

def test_type_get_data_from_single_entry(mock_single_entry_one):
    """020D test data type of the output"""
    assert type(get_data_from_single_entry(mock_single_entry_one)) == dict

def test_convert_csv():
    """test that output of function returns xlsx"""
    convert_csv()
    assert path.isfile('Cities/test.xlsx') == True
    if os.path.isfile('Cities/test.xlsx') == True:
        os.remove('Cities/test.xlsx')

def test_cities_exist():
    """test that cities directory exists"""
    assert path.isdir('Cities') == True