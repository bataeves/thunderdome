
def create_type(model):
    qs = []
    
    pass

def create_table(model, create_missing_keyspace=True):
    #construct query string
    cf_name = model.column_family_name()
    raw_cf_name = model.column_family_name(include_keyspace=False)

    #create missing keyspace
    if create_missing_keyspace:
        create_keyspace(model.keyspace)

    with connection_manager() as con:
        #check for an existing column family
        ks_info = con.con.client.describe_keyspace(model.keyspace)
        if not any([raw_cf_name == cf.name for cf in ks_info.cf_defs]):
            qs = ['CREATE TABLE {}'.format(cf_name)]

            #add column types
            pkeys = []
            qtypes = []
            def add_column(col):
                s = '{} {}'.format(col.db_field_name, col.db_type)
                if col.primary_key: pkeys.append(col.db_field_name)
                qtypes.append(s)
            for name, col in model._columns.items():
                add_column(col)

            qtypes.append('PRIMARY KEY ({})'.format(', '.join(pkeys)))
            
            qs += ['({})'.format(', '.join(qtypes))]
            
            # add read_repair_chance
            qs += ["WITH read_repair_chance = {}".format(model.read_repair_chance)]
            qs = ' '.join(qs)

            con.execute(qs)

        indexes = [c for n,c in model._columns.items() if c.index]
        if indexes:
            for column in indexes:
                #TODO: check for existing index...
                #can that be determined from the connection client?
                qs = ['CREATE INDEX {}'.format(column.db_index_name)]
                qs += ['ON {}'.format(cf_name)]
                qs += ['({})'.format(column.db_field_name)]
                qs = ' '.join(qs)
                con.execute(qs)


def delete_table(model):
    #check that model exists
    cf_name = model.column_family_name()
    raw_cf_name = model.column_family_name(include_keyspace=False)
    with connection_manager() as con:
        ks_info = con.con.client.describe_keyspace(model.keyspace)
        if any([raw_cf_name == cf.name for cf in ks_info.cf_defs]):
            con.execute('drop table {};'.format(cf_name))

