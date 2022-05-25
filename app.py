import urllib.request
import json
import os.path
from os import path
import csv
import pandas as pd
import glob
from datetime import datetime
import pathlib

def merge_files():
    frames = dict()
    path = os.path.dirname(os.path.abspath(__file__))
    files = glob.glob(path + "\Cities\*.xlsx")
    
    for i in range(len(files)):
        s = os.path.splitext(files[i])
        s = os.path.split(s[0])
        
        frames[s[1]] = files[i]
    
    writer = pd.ExcelWriter(path+"\\merging_file.xlsx", engine='xlsxwriter')

    for sheet, frame in frames.items():
        df = pd.read_excel(frame)
        df.to_excel(writer, sheet_name=sheet)
    writer.save()
    format_excel(path+"\\merging_file.xlsx")
    

def convert_csv():
    """
    This function converts all the csv files into an xlsx file

    :returns xlsx files
    """
    path = os.path.dirname(os.path.abspath(__file__))
    dir_path = path + "\Cities"
    files = glob.glob(dir_path + "\*.csv")

    for filename in files:
        df = pd.read_csv(filename)
        city = os.path.splitext(os.path.basename(filename))[0] # this gets rid of the .csv in the filename
        df.to_excel(dir_path+"\\"+city+".xlsx")
        format_excel(dir_path+"\\"+city+".xlsx")
        


def format_excel(filename):
    """
    This function takes the newly converted files and formats the document making each header have a drop down menu

    :returns styled files
    """
    xl = pd.ExcelFile(filename)
    s = os.path.splitext(filename)
    s = os.path.split(s[0])

    if s[1] != 'merging_file':
        df = pd.read_excel(filename)
        df.drop(['Unnamed: 0'], axis=1, inplace=True)
        
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')

        df.to_excel(writer, startrow=1, header=False, index=False)
        worksheet = writer.sheets['Sheet1']
        (max_row, max_col) = df.shape
        column_settings = [{'header': column} for column in df.columns]
        worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
        worksheet.set_column(0, max_col - 1, 12)
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).str.len().max(), len(col) + 2)
            worksheet.set_column(i, i, column_len)
    else:
        writer = pd.ExcelWriter('benchmarking.xlsx', engine='xlsxwriter')

        for i in range(len(xl.sheet_names)):
            df = pd.read_excel(xl, xl.sheet_names[i])
            df.drop(['Unnamed: 0'], axis=1, inplace=True)
            
            df.to_excel(writer, sheet_name=xl.sheet_names[i], startrow=1, header=False, index=False)
            worksheet = writer.sheets[xl.sheet_names[i]]
            (max_row, max_col) = df.shape
            column_settings = [{'header': column} for column in df.columns]
            worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
            worksheet.set_column(0, max_col - 1, 12)
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).str.len().max(), len(col) + 2)
                worksheet.set_column(i, i, column_len)
    writer.save()
    

def get_data_from_records():
    """This function reads the record.json file and returns a list of dictionaries
       Every dictionary is a single entry.

    Returns:
        [list]: list of entries
    """
    with open('record.json', 'rt', encoding='UTF8') as f:
        list_of_entries = json.load(f)
    return list_of_entries


def get_data_from_single_entry(single_entry):
    """This function gets the data from the API, and returns a dictionary with all the key-value pairs
 
    Args:
        single_entry (dict): this is a dictionary that represents one entry/row

    Returns:
        [dict]: this dict contains the exact data in the form of key-value pairs, which will be directly filled in the csv files
    """
    url = single_entry["api_endpoint"]
    file_type = pathlib.Path(url).suffix
    # get data from api
    try:
        if "json" in single_entry["api_endpoint"]:
            with urllib.request.urlopen(single_entry["api_endpoint"]) as url:
                    data = json.loads(url.read().decode())
        elif "csv" in single_entry["api_endpoint"]:
            data = pd.read_csv(single_entry["api_endpoint"], sep=',')
        elif ".xlsx" in single_entry["api_endpoint"]:
            data = pd.read_excel(single_entry["api_endpoint"])
        else:
            raise ValueError

        # this part checks if the value is an empty string, if it is the parse code is not evaluated and an hyphen is assigned instead
        if single_entry["metric_parse_code"] != "":
            metric_value = eval(single_entry["metric_parse_code"])
        else:
            metric_value = "-"

        if single_entry["metric_name"] != "" and "data[" in single_entry["metric_name"]:
            metric_name = eval(single_entry["metric_name"])
        else:
            metric_name = single_entry["metric_name"]
            
        if not single_entry["date_parse_code"].isdigit() and single_entry["date_parse_code"] != "":
            date_value = eval(single_entry["date_parse_code"])
        elif single_entry["date_parse_code"] == "":
            date_value = "-"
        else:
            date_value = single_entry["date_parse_code"]

        return {'Serial No.': "",
                # I left this value blank because I reassign the value of serial number in line 78, so it doesn't matter what is was initially
                'Metric Name': metric_name,
                'City': single_entry["city"],
                'Metric Value': metric_value,
                'Date': date_value,
                'CoV Dimension ID': single_entry["cov_dimension_id"] if single_entry["cov_dimension_id"] != "" else "-",
                # if the value is "", assigns "-"
                'CoV Metric Name': single_entry["cov_metric_name"] if single_entry["cov_metric_name"] != "" else "-",
                # if the value is "", assigns "-"
                'API Endpoint': single_entry["api_endpoint"]
                }
    except (ValueError, urllib.error.HTTPError, urllib.error.URLError, FileNotFoundError) as err:
        now = datetime.now()

        date_time = now.strftime("%m/%d/%Y %H:%M:%S")
        filename = "app.log"
        log_data = 'Timestamp: %s  Error - Invalid API endpoint: %s\n' % (date_time, single_entry["api_endpoint"])
        if path.exists(filename):
            write_file = 'a'
        else:
            write_file = 'w'

        with open(filename, write_file) as logfile:
            logfile.write(log_data)
            print("API Endpoint Error:", err, single_entry["api_endpoint"])


def make_dir_and_file(data_dict):
    df = pd.DataFrame(data_dict, index=[])

    path = os.path.dirname(os.path.abspath(__file__))
    dir_path = path + "\Cities"

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    filename = f"{data_dict['City']}.csv"
    file_path = dir_path + "\\" + filename
    if not os.path.exists(file_path):
        df.to_csv(file_path, mode='w', header=True, index=False)
    
    existing_data = pd.read_csv(file_path)
    return existing_data, file_path
 

def data_to_dict(serial_no, metric_name, city, metric_value, date, cov_dimension_id, cov_metric_name, api_endpoint):
    to_dict = dict()

    to_dict = {
        "Serial No." : serial_no,
        "Metric Name" : metric_name,
        "City" : city,
        "Metric Value" : metric_value,
        "Date" : date,
        "CoV Dimension ID" : cov_dimension_id,
        "CoV Metric Name" : cov_metric_name,
        "API Endpoint" : api_endpoint
    }
    return to_dict


def put_single_entry_in_csv(data_dict):
    """This function takes the dictionary generated in the get_data_from_single_entry function and puts in a csv file of the city.
       If the csv file doesn't exist, it creates one with a header. The keys in the data_dict are filled in as a header. If the file
       exists, it appends to the respective city's file.

    Args:
        data_dict (dict): This is the dict returned by get_data_from_single_entry function
    """
    
    existing_data, file_path = make_dir_and_file(data_dict)

    if type(data_dict["Metric Name"]) is str:
        if len(existing_data) == 0:
            data_dict["Serial No."] = len(existing_data) + 1
            df = pd.DataFrame(data_dict, index=[])
            df = df.append(data_dict, ignore_index=True)
            df.to_csv(file_path, mode='a', header=False, index=False)
            return

        for i in existing_data.index:
            existing_metric_name = existing_data['Metric Name'][i]
            existing_date = str(existing_data['Date'][i])
            existing_value = existing_data['Metric Value'][i]

            if existing_metric_name == data_dict['Metric Name'] and existing_date == data_dict[
                'Date']:  # if a existing_data has the same metric name and date as data_dict
                if existing_value != data_dict['Metric Value']:
                    existing_data.replace(existing_data['Metric Value'][i], data_dict['Metric Value'], inplace=True)
                    existing_data.to_csv(file_path, index=False)
                return

        data_dict["Serial No."] = len(existing_data) + 1
        existing_data = existing_data.append(data_dict, ignore_index=True)
        existing_data.to_csv(file_path, index=False)
    else:
        if len(existing_data) == 0:
            serial_no = 1
            for i in range(len(data_dict["Metric Name"])):
                dict_format = data_to_dict(serial_no, data_dict["Metric Name"][i], data_dict["City"], data_dict["Metric Value"][i], data_dict["Date"], data_dict["CoV Dimension ID"], data_dict["CoV Metric Name"], data_dict["API Endpoint"])
                df = pd.DataFrame(dict_format, index=[])
                df = df.append(dict_format, ignore_index=True)
                df.to_csv(file_path, mode='a', header=False, index=False)
                serial_no = serial_no + 1
            return

        for i in existing_data.index:
            existing_metric_name = existing_data['Metric Name'][i]
            existing_date = str(existing_data['Date'][i])
            existing_value = existing_data['Metric Value'][i]
            # Update data_dict["Metric Name"] and ["Metric Value"]
            for i in range(len(data_dict["Metric Name"])):
                if existing_metric_name == data_dict['Metric Name'][i] and existing_date == data_dict[
                    'Date']:  # if a existing_data has the same metric name and date as data_dict
                    if existing_value != data_dict['Metric Value'][i]:
                        existing_data.replace(existing_data['Metric Value'][i], data_dict['Metric Value'][i], inplace=True)
                        existing_data.to_csv(file_path, index=False)
                    return

        serial_no = len(existing_data) + 1

        for i in range(len(data_dict["Metric Name"])): 
            dict_format = data_to_dict(serial_no, data_dict["Metric Name"][i], data_dict["City"], data_dict["Metric Value"][i], data_dict["Date"], data_dict["CoV Dimension ID"], data_dict["CoV Metric Name"], data_dict["API Endpoint"])
            existing_data = existing_data.append(dict_format, ignore_index=True)
            existing_data.to_csv(file_path, index=False)
            serial_no = serial_no + 1
    

if __name__ == "__main__":
    list_of_entries = get_data_from_records()
    # the loop below passes a single entry to every function. The loop runs until the list of entries is exhausted
    for single_entry in list_of_entries:
        try:
            data_dict = get_data_from_single_entry(single_entry)
            put_single_entry_in_csv(data_dict)
        except TypeError:
            pass
    convert_csv()
    merge_files()
    os.remove("merging_file.xlsx")
    
