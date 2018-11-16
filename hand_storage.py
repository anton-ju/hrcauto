# -*- coding: utf-8 -*-
"""
Created on Fri Jul 13 00:33:55 2018

@author: user
"""
import glob
import os
import psycopg2


class HandStoragePgsql():
    def __init__(self, dbname, user, host, port, pwd):
        try:
            self.conn = psycopg2.connect(
                f"dbname='{dbname}' user='{user}' host='{host}' port='{port}' password='{pwd}'")
        except:
            raise psycopg2.Error('Connection error')

    def read_hand(self, date):
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT hh_id, "
                            "date_played, "
                            "room_id, "
                            "gamenumber, "
                            "hh FROM handhistory "
                            f"WHERE date_played > '{date}'")
                for record in cur:
                    yield record[4]

    def read_summary(self, tid):
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT tournament_id, summary "
                            "FROM tournament_summaries "
                            f"WHERE tournament_id = {tid}")
                if cur.rowcount > 0:
                    return cur.fetchone()[1]
                else:
                    return None


class HandStorage(object):
    
    def __init__(self, path=''):
        
        if path:
            if not os.path.exists(path):
                raise IOError
        
            self.path = path
        else: 
            self.path = os.getcwd()

    def read_hand(self):

        fi = glob.glob(f'{self.path}/**/*.txt', recursive=True)
  
        for file in fi:

            with open(file, encoding='utf-8') as f:

                try:
                    
                    s = f.read()
                    s = s.split('\n\n')
                    for ss in s:
                        if ss == '\n\n' or ss==None or ss == '':
                            continue
                        yield ss
                        
                except:
                    continue
        
        
                
    
