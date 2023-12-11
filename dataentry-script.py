from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

def iniciar_navegador():
    try:
        driver = webdriver.Chrome()
        return driver
    except WebDriverException:
        input("Falta el ChromeDriver para ejecutar el programa. Apretá ENTER para instalarlo...")
        print("Instalando ChromeDriver...")
        return webdriver.Chrome(ChromeDriverManager().install())

def seleccionar_opcion(id_menu, valor):
    try:
        # Esperar hasta que el menú sea visible y clickeable
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, id_menu)))
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id_menu)))
        menu = driver.find_element(By.ID, id_menu)

        # Crear instancia de Select y seleccionar la opción
        select = Select(menu)
        select.select_by_value(valor)

    except Exception as e:
        print(f"Error al seleccionar opción en menú '{id_menu}': {e}")
        input()

def procesar_preguntas():

    # Establecer un contador de preguntas
    numero_pregunta = 0

    def cargar_pregunta(datos_pregunta):

        try:
            print(f"Ingresando datos de pregunta {numero_pregunta}")

            # Establecer el nivel de dificultad según el número de pregunta 
            # Las preguntas 1-5 son Básico, 6-10 son Intermedio y las restantes son Avanzado
            if numero_pregunta <= 5:
                nivel = "1"
            elif numero_pregunta <= 10:
                nivel = "2"
            else:
                nivel = "3"

            # Localizar el menú de dificultad desplegable por XPath, crear instancia de Select y seleccionar la opción correspondiente
            menu = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "(//select[@id='level_id'])[2]")))
            select = Select(menu)
            select.select_by_value(nivel)

            # Ingresar la pregunta
            campo_pregunta = driver.find_elements(By.CLASS_NAME, "note-editable")[0]
            accion = ActionChains(driver)
            accion.click(campo_pregunta).send_keys(datos_pregunta['pregunta']).perform()

            # Seleccionar el tipo de pregunta según la cantidad de opciones correctas
            # Si solo hay una opción correcta es "radio" (valor 3 en el menú de la página)
            # Si tiene múltiples opciones correctas es "checkbox" (valor 1 en el menú de la página)
            tipo = "3" if len(datos_pregunta['respuesta_correcta']) == 1 else "1"
            seleccionar_opcion('type_id', tipo)

            # Seleccionar el tópico (siempre el tercero en el menú de la página)
            seleccionar_opcion('topic_id', '3')

            # Ingresar puntos de la pregunta (siempre será 10)
            puntos = driver.find_elements(By.ID, "points")
            puntos[1].send_keys("10")

            # Seleccionar la cantidad de respuestas/opciones
            cantidad_respuestas = str(len(datos_pregunta['opciones']))
            seleccionar_opcion('cant_questions', cantidad_respuestas)

            # Ingresar respuestas/opciones y marcar la(s) correcta(s)
            for i, opcion in enumerate(datos_pregunta['opciones'], start=1):
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.NAME, f"answer[{i}]text")))
                driver.find_element(By.NAME, f"answer[{i}]text").send_keys(opcion)
                # Chequear si la respuesta ingresada es correcta
                if i in datos_pregunta['respuesta_correcta']:
                    driver.find_element(By.NAME, f"is_correct[{i}]correct").click()
            
            # Ingresar explicación si existe
            if 'explicacion' in datos_pregunta:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "explicacion")))
                driver.find_element(By.ID, "explicacion").send_keys(datos_pregunta['explicacion'])

            # Ingresar número en el campo objetivos (siempre será 1)
            driver.find_element(By.ID, "objetivos").send_keys("1")

            # Guardar la pregunta
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            boton_guardar = driver.find_element(By.XPATH, "//button[contains(text(), 'Guardar')]")
            driver.execute_script("arguments[0].click();", boton_guardar)

            print(f"Pregunta {numero_pregunta} cargada con éxito.")

            # Clickear en nueva pregunta para que se habiliten los campos de la nueva pregunta a cargar
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "new_question"))).click()

        except Exception as e:
            print(f"Error al procesar pregunta {numero_pregunta}: {e}")
            input()

    # Abrir el archivo y procesar cada línea
    with open(f"{examen}.txt", 'r', encoding='utf-8') as archivo:
        datos_pregunta = {}
        opciones = []
        datos_pregunta['respuesta_correcta'] = []
        for linea in archivo:
            linea = linea.strip()
            # Chequear si la línea es una pregunta (Formato: Pregunta 1: ...). 
            # Se inicia la recopilación de datos
            if linea.startswith('Pregunta'):
                numero_pregunta += 1
                datos_pregunta = {}
                opciones = []
                datos_pregunta['respuesta_correcta'] = []
                # Extraer pregunta
                datos_pregunta['pregunta'] = linea.split(":", 1)[1].strip()
            
            # Chequear si la línea es una opción (Formato: A) B) C) etc.), evitando la opción correcta para no tenerla duplicada
            # Detectar si es una respuesta correcta o incorrecta y eliminar ese texto
            # Agregar la línea a la lista de opciones de la pregunta

            elif ')' in linea and len(linea.split(')')[0]) == 1 and not linea.startswith('Opción correcta:'):
                _, opcion_texto = linea.split(')', 1)
                if "(Respuesta correcta)" in opcion_texto:
                    datos_pregunta['opcion_correcta'] = len(opciones) + 1
                    opcion_texto = opcion_texto.replace("(Respuesta correcta)", "").strip()
                elif "(Respuesta incorrecta)" in opcion_texto:
                    opcion_texto = opcion_texto.replace("(Respuesta incorrecta)", "").strip()
                opciones.append(opcion_texto.strip())
            
            # Chequear si la línea es una opción (Formato: 1. 2. 3. etc.), evitando la opción correcta para no tenerla duplicada
            # Detectar si es una respuesta correcta o incorrecta y eliminar ese texto
            # Agregar la línea a la lista de opciones de la pregunta
            elif '.' in linea and linea.strip().split('.')[0].isdigit():
                _, opcion_texto = linea.split('.', 1)
                if "(Respuesta correcta)" in opcion_texto:
                    datos_pregunta['respuesta_correcta'].append(len(opciones) + 1)
                    opcion_texto = opcion_texto.replace("(Respuesta correcta)", "").strip()
                elif "(Respuesta incorrecta)" in opcion_texto:
                    opcion_texto = opcion_texto.replace("(Respuesta incorrecta)", "").strip()
                opciones.append(opcion_texto.strip())
        
            # Chequear si la línea es una opción correcta (puede haber más de una)
            # (Formato de la línea con opción correcta: Opción correcta: A)...)
            elif linea.startswith('Opción correcta:'):
                try:
                    letra_respuesta = linea.split(':')[1].split(")")[0].lower().strip()
                    indice_correcto = 'abcdefgh'.index(letra_respuesta) + 1
                    datos_pregunta['respuesta_correcta'].append(indice_correcto)
                except:
                    num_respuesta = linea.split(':')[1].split(")")[0].strip()
                    datos_pregunta['respuesta_correcta'].append(int(num_respuesta))
            
            # Chequear si la línea es una explicación (Formato: Explicación: ...)
            elif linea.startswith('Explicación:'):
                datos_pregunta['explicacion'] = linea.split(':', 1)[1].strip()
            
            # Fin de la pregunta, agregar la lista opciones al diccionario de la pregunta y llamar a la función que cargará todos los datos en la página
            elif linea.startswith('!'):
                datos_pregunta['opciones'] = opciones
                cargar_pregunta(datos_pregunta)

# Inicio del programa, del navegador y acceso a la URL
url = input("Hola Carito :)\nPegá acá el link donde tenés que cargar las preguntas: ")
examen = input("Ahora escribí tal cual el nombre del archivo (sin el '.txt') que tiene el examen: ")

while examen:
    try:
        chequeo_archivo = open(f"{examen}.txt", "r")
        chequeo_archivo.close()
        break
    except:
        examen = input("No encuentro el archivo, fijate que esté guardado en la misma carpeta que este programa y que esté en formato '.txt'\nPoné de nuevo el nombre (corroborá que esté escrito tal cual, y sin el '.txt' al final): ")

try:
    driver = iniciar_navegador()
    driver.get(url)
    driver.maximize_window()

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "username"))).send_keys("carolina.liendo@educacionit.com")
    driver.find_element(By.ID, "password").send_keys("42912C5")
    driver.find_element(By.ID, "loginButton").click()

    driver.get(url)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "new_question"))).click()

    procesar_preguntas()

except Exception as e:
    print(f"Se ha producido un error: {e}")

finally:
    input("Listo Carito, se cargaron todas las preguntas :)\nApretá ENTER para cerrar el programa.\n")
    driver.quit()