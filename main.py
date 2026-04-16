import google_colab_selenium as gs
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from IPython.display import Image
import time
import json

def criar_driver():
    options = Options()
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    return gs.Chrome(options=options)

driver = criar_driver()

driver.get('https://www.imdb.com/')

WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.ID, "imdbHeader"))
)

driver.save_screenshot("tela.png")
Image("tela.png")

driver.find_element(By.ID, "imdbHeader-navDrawerOpen").click()

driver.save_screenshot("menu.png")

Image("menu.png")

driver.find_element(By.XPATH, "//label[@aria-label='Expand Movies nav links']").click()

driver.save_screenshot("menuMov.png")

Image("menuMov.png")

driver.find_element(By.XPATH, "//a[@aria-label='Go to Top 250 movies']").click()

WebDriverWait(driver, 15).until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "ul.ipc-metadata-list li.ipc-metadata-list-summary-item")
    )
)

driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(1)

driver.save_screenshot("top250.png")

Image("top250.png")

rows = driver.find_elements(
    By.CSS_SELECTOR,
    "ul.ipc-metadata-list li.ipc-metadata-list-summary-item"
)

filmes_ranking = []

for i, row in enumerate(rows, start=1):
    try:
        titulo = row.find_element(By.CSS_SELECTOR, "h3.ipc-title__text").text.strip()
        rank = i

        # URL da página do filme
        url = row.find_element(
            By.CSS_SELECTOR, "a.ipc-title-link-wrapper"
        ).get_attribute("href").split("?")[0]

        filmes_ranking.append({"rank": rank, "titulo": titulo, "url": url})

    except Exception as e:
        print(f"Erro na linha {len(filmes_ranking)+1}: {e}")

print(f"{len(filmes_ranking)} filmes encontrados no ranking!")

def scrape_filme(driver, filme):
    driver.get(filme["url"])
    time.sleep(1)

    try:
        titulo = driver.find_element(By.XPATH, "//h1[@data-testid='hero__primary-text']/span").text.strip()
    except:
        titulo = filme["titulo"]

    try:
        ano = driver.find_element(By.XPATH, "//a[contains(@href,'releaseinfo')]").text.strip()[:4]
    except:
        ano = ""

    try:
        elemento = driver.find_element(By.XPATH, "//div[@data-testid='hero-rating-bar__aggregate-rating__score']/span[1]")
        nota = driver.execute_script("return arguments[0].innerText;", elemento)
    except:
        nota = ""

    try:
        elementos_generos = driver.find_elements(By.XPATH, "//div[@data-testid='interests']//span[@class='ipc-chip__text']")
        generos = [g.text.strip() for g in elementos_generos if g.text.strip()]
    except:
        generos = []

    try:
        diretores = [d.text.strip() for d in driver.find_elements(By.XPATH, "//li[@data-testid='title-pc-principal-credit'][.//span[contains(text(),'Director') or contains(text(),'Diretor')]]//a") if d.text.strip()]
    except:
        diretores = []

    try:
        poster_url = driver.find_element(By.XPATH, "//a[contains(@href,'mediaviewer')]").get_attribute("href")
    except:
        poster_url = ""

    return {
        "rank": filme["rank"], "titulo": titulo, "ano": ano,
        "nota_imdb": nota, "generos": generos, "diretores": diretores,
        "poster_url": poster_url, "url": filme["url"]
    }


# JSON
final = "top250_listagem.json"
filmes_completos = []

driver = criar_driver()

for i, filme in enumerate(filmes_ranking, start=1):
    for tentativa in range(3):
        try:
            resultado = scrape_filme(driver, filme)
            filmes_completos.append(resultado)
            print(f"[{i:>3}/250]")
            break

        except Exception as e:
            print(f"[{i:>3}/250] Tentativa {tentativa+1}/3 falhou: {e}")
            try:
                driver.quit()
            except:
                pass
            time.sleep(3)
            driver = criar_driver()


with open(final, "w", encoding="utf-8") as f:
    json.dump(filmes_completos, f, ensure_ascii=False, indent=2)
print(f"{len(filmes_completos)} filmes salvos em {final}")

driver.quit()
