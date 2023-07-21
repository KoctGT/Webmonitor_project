import sqlite3


def get_all_fields_from_table(db, table):
    query_select_all = "SELECT * FROM {}".format(table)
    return select_query_all(db, query_select_all)

def select_query_all(db, query):
    try:
        connection = sqlite3.connect(db)
        cur = connection.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        connection.close()
        
        return rows
    except sqlite3.IntegrityError as err:
        print("Select action error: ", err)
    finally:
        if connection:
            connection.close()
        
def add_data_in_table(db, data, table):
    param_string, _, blank, _ = _generate_insert_and_upd_query_blank(data)
    insert_value_list, _ =_forming_insert_and_upd_value_lists(
        data=data,
        keys_list=param_string.split(",")
        )
    # print("\ninsert_value_list= ", insert_value_list, "\n")
    query_insert = f"INSERT INTO {table} ({param_string}) values ({blank})"
    # print("\nquery_insert = ", query_insert, '\n')
    add_or_update_data(db, query_insert, insert_value_list)

def update_data_in_table(db, data, table, condition):
    #print('data= ', data)
    param_string, param_string_upd, _, blank_upd = _generate_insert_and_upd_query_blank(data)
    _, update_value_list =_forming_insert_and_upd_value_lists(
        data=data,
        keys_list=param_string.split(",")
        )
    # print("1update_value_list= ", update_value_list)
    query_update = f"UPDATE {table} SET ({param_string_upd}) = ({blank_upd}) WHERE {condition} = ?"
    # print("1query_update = ", query_update)
    add_or_update_data(db, query_update, update_value_list)

def add_or_update_data(db, query, data=None):
    connection = sqlite3.connect(db)
    # print('\nquery= ', query)
    # print('\ndata= ', data)
    if data:
        for row in data:
            try:
                with connection:
                    connection.execute(query, row)
            except sqlite3.IntegrityError as err:
                print("При добавлении данных:", row, "Возникла ошибка:", err)
                pass
    else:
        try:
            with connection:
                    connection.execute(query)
        except sqlite3.IntegrityError as err:
            print("При добавлении данных:", row, "Возникла ошибка:", err)
    connection.close()        

def sync_db_records(db, data, table):
    param_string, param_string_upd, blank, blank_upd = _generate_insert_and_upd_query_blank(data)
    insert_value_list, update_value_list =_forming_insert_and_upd_value_lists(
        data=data,
        keys_list=param_string.split(",")
        )
    uniqual_field = param_string.split(',')[0]
    find_query = f"SELECT {uniqual_field} FROM {table}"
    disable_query = f"UPDATE {table} SET enabled = 0 WHERE {uniqual_field} = ?".replace('?', "'{}'")
    # print("\ninsert_value_list= ", insert_value_list)
    unique_field_values = []
    for row in data:
        unique_field_values.append(row.get(uniqual_field))
    # print("unique_fields= ", unique_fields)
    _disable_entries_outside_the_list(db=db,
                                      find_query=find_query,
                                      disable_query=disable_query,
                                      unique_fields=unique_field_values,
                                      )

    sql_query_insert = f"INSERT OR FAIL INTO {table} ({param_string}) VALUES ({blank});"
    sql_query_update = f"UPDATE {table} SET ({param_string_upd}) = ({blank_upd}) WHERE {uniqual_field} = ?;"
    # print("sql_query_insert = ", sql_query_insert)
    # print("sql_query_update = ", sql_query_update)
    # print("insert_value_list, update_value_list = ", insert_value_list, update_value_list)
    add_or_update_data(db, sql_query_insert, insert_value_list)
    add_or_update_data(db, sql_query_update, update_value_list)

def _generate_insert_and_upd_query_blank(data:list):
    param_list = list(data[0].keys())
    # print("param_list= ", param_list)
    param_list_upd = param_list[1:]
    param_list_upd.reverse()
    # print("param_list_upd= ", param_list_upd)

    param_string = ",".join(param_list)
    param_string_upd = ",".join(param_list_upd)
    # print("param_string = ", param_string)
    blank = ("?," * len(param_list)).rstrip(",")
    blank_upd = ("?," * len(param_list_upd)).rstrip(",")
    # print("blank = ", blank)
    # print("base_param_list = ", param_list)
    
    return param_string, param_string_upd, blank, blank_upd

def _forming_insert_and_upd_value_lists(data:list, keys_list:list):
    insert_value_list = []
    update_value_list = []
    # print('\ndata= ', data)
    # print('\nkeys_list= ', keys_list)
    for row in data:
        if row:
            temp_insert_list = []
            temp_update_list = []
            err = False
            for pname in keys_list:
                if pname:
                    temp_insert_list.append(row[pname])
                    temp_update_list.insert(0, row[pname])
                else:
                    err = True
                    break
            if not err:
                insert_value_list.append(temp_insert_list)
                update_value_list.append(temp_update_list)
            else:
                insert_value_list.append([])
                update_value_list.append([])    
        else:
            insert_value_list.append([])
            update_value_list.append([])
    # print("insert_value_list = ", insert_value_list)
    # print("update_value_list = ", update_value_list)
    return insert_value_list, update_value_list

def _disable_entries_outside_the_list(db, find_query, disable_query, unique_fields: list):
    query_result_list = select_query_all(db, find_query)
    # print("query_result_list= ", query_result_list)
    if query_result_list:
        for qres in query_result_list:
            if qres[0] not in unique_fields:
                # print("qres[0]= ", qres[0])
                disable_query_row = disable_query.format(qres[0])
                # print("disable_query_row =", disable_query_row)
                add_or_update_data(db=db, query=disable_query_row)