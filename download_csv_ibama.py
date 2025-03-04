from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configuração do navegador
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # Maximiza a janela do navegador

# Inicializa o navegador com o ChromeDriverManager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Acessa a página do IBAMA
    driver.get("https://servicos.ibama.gov.br/ctf/publico/areasembargadas/ConsultaPublicaAreasEmbargadas.php")
    
    # Aguarda alguns segundos para garantir que a página carregue completamente
    time.sleep(5)
    
    # Localiza o botão "Formato CSV" e clica nele
    csv_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Formato CSV')]")
    csv_button.click()
    
    # Aguarda o download do arquivo (ajuste o tempo conforme necessário)
    time.sleep(10)
    
    print("Download do arquivo CSV realizado com sucesso!")

finally:
    # Fecha o navegador
    driver.quit()