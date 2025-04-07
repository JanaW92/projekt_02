import mysql.connector
import pytest


#vytvoření připojení na databázi
def pripojeni_db():
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",                #doplnit heslo
            database="projekt_02"
            )
        return connection
    

#vytvoření tabulky
def vytvoreni_tabulky(connection, test_mode=False):
    table_name = "ukoly_test" if test_mode == True else "ukoly"
    cursor = connection.cursor()
    cursor.execute(f"""
                   CREATE TABLE IF NOT EXISTS {table_name}
                   (
                   id INT AUTO_INCREMENT PRIMARY KEY,
                   nazev VARCHAR(50) NOT NULL,
                   popis VARCHAR(100) NOT NULL,
                   stav ENUM('nezahájeno', 'probíhá', 'hotovo') DEFAULT 'nezahájeno', 
                   datum_vytvoreni TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
            """)
    connection.commit()
    cursor.close()


#přidání ukolu
def pridat_ukol(connection, nazev, popis, stav = 'nezahájeno', test_mode = False):
    if not nazev.strip() or not popis.strip():      #ověřím že nebudu hodnoty prázdné
        raise ValueError("Název a popis úkolu jsou povinné údaje.")
    
    table_name = "ukoly_test" if test_mode==True else "ukoly"
    cursor = connection.cursor()
    try:
        cursor.execute(f"INSERT INTO {table_name} (nazev, popis, stav) VALUES (%s,%s,%s)",(nazev, popis,stav,))
        connection.commit()
        print(f"Název úkolu: {nazev}, popis úkolu: {popis} a stav úkolu: {stav}, byli přidáný do tabulky {table_name}.")        
    except mysql.connector.Error as e:
        print(f"Chyba: {e}")
    cursor.close()
    
#zobrazení úkolů
def zobrazit_ukoly(connection, id, test_mode = False ):
    table_name = "ukoly_test" if test_mode==True else "ukoly"
    cursor = connection.cursor(dictionary = True)       #vráti mi výsledek jako slovník 'id': 1

    cursor.execute(f"SELECT * FROM {table_name} WHERE stav in ('nezahájeno', 'probíhá')")
    ukoly = cursor.fetchall()           #seznam všech řádků 
    cursor.close()
    return ukoly


#aktualizace úkolu
def aktualizovat_ukol(connection, id_vyber, novy_stav, test_mode = False):
    table_name = "ukoly_test" if test_mode==True else "ukoly"
    cursor = connection.cursor(dictionary = True)
    
    cursor.execute(f"UPDATE {table_name} SET stav = %s WHERE id = %s",( novy_stav,id_vyber,))       #uděláme aktualizaci
    connection.commit()

    cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s",(id_vyber,))       #po aktualizaci uděláme select
    aktualizovany_ukol = cursor.fetchone()
    
    cursor.close()

    if not aktualizovany_ukol:
        print(f"Úkol s ID {id_vyber} neexistuje")
        return None
    return aktualizovany_ukol


#odstránení úkolu
def odstranit_ukol(connection, id, test_mode = False): 
    table_name = "ukoly_test" if test_mode==True else "ukoly"
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (id,))
    connection.commit()
    cursor.close()
    print(f"\nÚkol s ID {id} byl smazán z tabulky {table_name}.")
    


#Pytest fixture pro testovací databázi
@pytest.fixture(scope="module")
def connection():
    connection = pripojeni_db()
    vytvoreni_tabulky(connection, test_mode=True)
    yield connection

    #když testy skončí, odstranim tabulku ukoly_test
    cursor = connection.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS ukoly_test")
        connection.commit()
    except mysql.connector.Error as e:
        print(f"Chyba při mazání testovací tabulky: {e}")
    cursor.close()
    connection.close()


# TESTY PYTESTEM

#testování pozitivního scénaře pro přidání úkolu
def test_pridat_ukol(connection):
    pridat_ukol(connection,"Test přidání úkolu", "Test přidání popisu", stav = "nezahájeno", test_mode=True)
    ukol = zobrazit_ukoly (connection, 1, test_mode=True)       #zavolám si ukol který jsem si vytvořila v předchozím kroku 
    assert ukol [0]["nazev"] == "Test přidání úkolu"
    assert ukol [0]["popis"] == "Test přidání popisu"


#testování negativních scénařů pomocí parametrize
@pytest.mark.parametrize("nazev, popis",
        [
            (" ", "negativní testování"),
            (" ", " "),
            ("negat", " ")
        ]
)
def test_negativni_pridani_ukolu(connection, nazev, popis):
    ukol = zobrazit_ukoly(connection, 1, test_mode=True)
    with pytest.raises(ValueError):
        pridat_ukol(connection, nazev, popis, stav = "nezahájeno", test_mode=True)


#testování pozitívni aktualizace úkolů
def test_aktualizovat_ukol(connection):
    pridat_ukol(connection, "Test aktualizace simple", "Popis aktualizace", "nezahájeno", test_mode=True )          #přidám úkol který pak budu aktualizovat

    ukoly = zobrazit_ukoly(connection, id=1, test_mode=True)        #dostanu ID ukolu který jsem přidala
    ukol_id = ukoly [0]["id"]

    aktualizovany_ukol = aktualizovat_ukol(connection, ukol_id, "hotovo", test_mode=True)       #provedu aktualizaci

    assert aktualizovany_ukol is not None
    assert aktualizovany_ukol["stav"] == "hotovo"


#testování negativní aktualizace
def test_negativni_aktualizace_ukolu(connection):
    non_exist_id = 555555
    vysledek = aktualizovat_ukol(connection, non_exist_id, "hotovo", test_mode=True)
    assert vysledek is None

#testování pozitívniho odstranení úkolu
def test_odstranit_ukol(connection):
    pridat_ukol(connection, "Odstránení úkolu", "odstránení popisu", test_mode = True)
    po_odstraneni = odstranit_ukol(connection, 2, test_mode= True )
    assert po_odstraneni is None

#testování negativního scénaře pro odstranení úkolů
def test_negativni_odstraneni_ukolu(connection):
    non_exist_id = 987654321
    deleted =odstranit_ukol(connection, non_exist_id, test_mode= True)
    print("\n Pokus o odstranění neexistujícího úkolu.")
    print(f"Výsledek: {deleted}")

    assert deleted is None


#možnosti testů pro výběr
TESTY = {
    "1": "test_pridat_ukol",
    "2": "test_negativni_pridani_ukolu",
    "3": "test_aktualizovat_ukol",
    "4": "test_negativni_aktualizace_ukolu",
    "5": "test_odstranit_ukol",
    "6": "test_negativni_odstraneni_ukolu"
}

#def hlavni_menu()

if __name__ == "__main__":
    conn = pripojeni_db()
    vytvoreni_tabulky(conn)

    while True:
        print ("\n Správce úkolů - Hlavní menu \n 1. Přidat nový úkol \n 2. Zobrazit úkoly \n 3. Aktualizovat úkol \n 4. Odstranit úkol \n 5. Spustit testy \n 6. Ukončit program  \n")

        volba = input("\n Vyberte možnost (1-6): ")

        if volba == "1":        #přidat nový úkol
            while True:
                
                nazev = input("Zadejte název úkolu: ").strip()      #ošetřím mezery 
                
                if not nazev:
                    print("Název úkolu je povinný údaj. \n")
                    continue
                
                popis = input("Zadejte popis úkolu: ").strip()
                
                if not popis:
                    print("Popis úkolu je povinný údaj. \n")
                    continue
                
                stav = input("Zadejte stav z následujícich možností jinak bude nastavena hodnota nezahájeno: \n hotovo \n probíhá \n").strip()

                if not stav or stav not in ["hotovo", "probíhá"]:
                    print("Výchozí stav úkolu je nastaveno na 'nezahájeno'")
                    stav = 'nezahájeno'
                    
                     
                break    
            pridat_ukol(conn, nazev, popis, stav)
        
          
        elif volba == "2":      #zobrazit úkol
            ukoly = zobrazit_ukoly(conn, id )
            if not ukoly:
                print("Žádné úkoly nejsou v databázi.")
            else:
                for ukol in ukoly:
                        print(f"ID {ukol['id']}, název úkolu: {ukol['nazev']},popis úkolu: {ukol['popis']},stav úkolu:  {ukol['stav']}")
  
        
        elif volba == "3":          #aktualizovat ukol
           ukoly = zobrazit_ukoly(conn, id)         #zobrazí všechny úkoly
           if not ukoly:
                print("Žádné úkoly nejsou v databázi.")
           else:
                for ukol in ukoly:
                    print(f"ID {ukol['id']}, název úkolu: {ukol['nazev']},popis úkolu: {ukol['popis']},stav úkolu:  {ukol['stav']}")

           
           while True:
                id_vyber = input("Vložte ID úkolu, který chcete aktualizovat: \n")

                if not id_vyber:
                    print("Neplatné ID úkolu. Zadejte správné ID.")
                    continue
           
                id_vyber= int(id_vyber)     #převedeme ID na celé číslo

                existuje = any(ukol["id"] == id_vyber for ukol in ukoly )

                if not existuje:
                    print("Úkol s tímto ID neexistuje. Zkuste to znovu.")
                    continue

                print(f"Vyberte nový stav pro úkol ID {id_vyber}: ")
                print( "1. Probíhá")
                print("2. Hotovo")

                novy_stav = input("Nový stav (probíhá/hotovo): ")

                if novy_stav in ["probíhá", "hotovo"]:
                    if aktualizovat_ukol(conn, id_vyber, novy_stav ):
                        print(f"Úkol s ID {id_vyber} byl změnen na stav {novy_stav}")
                    else:
                        print("Chyba při aktualizaci úkolu.")
                    break
                else:
                    print("Neplatný stav. Stav musí být 'probíhá', nebo 'hotovo'.")
                    continue
        
        elif volba == "4":      #odstranit úkol
            ukoly = zobrazit_ukoly(conn, id)            #zobrazí všechny úkoly
            
            if not ukoly:
                print("Žádné úkoly nejsou v databázi.")
            else:
                for ukol in ukoly:
                        print(f"ID {ukol['id']}, název úkolu: {ukol['nazev']},popis úkolu: {ukol['popis']},stav úkolu:  {ukol['stav']}")
            
            while True:
                id_odstraneni =input("Zadejte ID úkolu, které chcete odstranit: \n")
                
                if any(str(ukol["id"])== id_odstraneni for ukol in ukoly):
                    odstranit_ukol(conn, id_odstraneni)
                    print(f"Úkol s ID {id_odstraneni} byl úspěšně odstraněn.")
                    break
                else:
                    print(f"ID {id_odstraneni} neexistuje. Vyberte správné ID.")
                    break
        
        elif volba == "5":   #spustit testy
            print("\n Možnosti testů: ")
            for key, value in TESTY.items():
                print (f"{key}: {value}")

            test_choice = input("Vyber možnost testu: ")

            if test_choice in TESTY:
                print(f"Spouštím test: {TESTY[test_choice]} \n")
                try:  
                    pytest.main(["-s", "-v", __file__, "-k", TESTY[test_choice]])
                except Exception as e:
                    print(f"Chyba při spuštění testu: {e}")

                input("\n Test dokončen. Stiskni Enter pro návrat do menu.")
            
            
        elif volba == "6":      #ukončit program
            print ("\nUkončit program.\n")
            conn.close
            break
        
        else: 
            print ("\n Neplatná volba, zvolte možnost (1-6)\n")

        
        


        




