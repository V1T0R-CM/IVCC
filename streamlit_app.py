import streamlit as st
import zipfile
import pandas as pd
import numpy as np
import statistics
import io

# Função para calcular estatísticas com base nos dados de entrada
def calc(data, Ucurto):
    if data is not None:
        # Extrair as colunas 'U', 't', e 'I' do DataFrame 'data'
        U = data['U']
        tempo = data['t']
        I = data['I']
        
        # Inicializar listas vazias para armazenar dados de tempo relacionados ao curto-circuito
        tempoteste = []
        indice = []
        tempocurto = []
        tempoarco = []
        
        # Encontrar os tempos de ocorrência de curto-circuito e armazená-los em 'tempoteste' e seus índices em 'indice'
        for i in range(len(tempo)):
            if U[i] < Ucurto:
                tempoteste.append(tempo[i])
                indice.append(i)
        o = len(indice)
        
        l = 0
        # Calcular os tempos de curto-circuito ('tempocurto') e os tempos de arco ('tempoarco')
        for j in range(o - 1):
            if j == o:
                tempocurto.append(tempoteste[o] - tempoteste[l])
            else:
                if indice[j + 1] - indice[j] > 1:
                    tempocurto.append(tempoteste[j] - tempoteste[l])
                    tempoarco.append(tempoteste[j + 1] - tempoteste[j])
                    l = j + 1
        
        # Calcular algumas estatísticas com base nos dados 'I' e 'U'
        array_I = np.array(I)
        array_U = np.array(U)
        imed = np.sum(array_I)/len(array_I)
        umed = np.sum(array_U)/len(array_U)
        ief = np.sqrt(np.sum(pow(array_I,2))/ len(array_I))
        uef = np.sqrt(np.sum(pow(array_U,2))/ len(array_U))
        pmed = np.sum(array_U*array_I)/len(array_U)
        # Calcular algumas estatísticas com base nos dados 'tempocurto' e 'tempoarco'
        tab = statistics.mean(tempoarco)
        devcc = statistics.pstdev(tempocurto)
        devab = statistics.pstdev(tempoarco)
        tcc = statistics.mean(tempocurto)
        ivcc = (devcc / tcc) + (devab / tab)

        # Retorna um dicionário com as estatísticas calculadas
        return {"Ief": ief, "Uef": uef, "Imed": imed, "Umed": umed, "Pmed": pmed, "IVcc": ivcc, "tcc": tcc}

# Função para converter um DataFrame para um arquivo Excel
def convertToExcel(dataframe):
    data_excel = io.BytesIO()
    with pd.ExcelWriter(data_excel, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Sheet1')
    data_excel.seek(0)
    return data_excel

# Função principal que exibe a interface do usuário (UI) utilizando Streamlit
def ivc():
    # Exibe o título do módulo
    st.write("# IVC")

    # Exibe o input do patamar de curto-circuito
    st.write("## Select the short-circuit threshold:")
    Ucurto = float(st.text_input("Short Threshold", "10"))

    # Exibe a seleção do tipo de arquivo
    st.write("## Select the file type:")
    choice = st.radio("File Types Available", ("Compressed folder(.zip)", "File(.txt)"))

    # Exibe o uploader de arquivos
    st.write("## Select the file:")

    if choice == "Compressed folder(.zip)":
        # Faz o upload do arquivo ZIP
        uploaded_file = st.file_uploader(f"Choose a Compressed folder(.zip)", accept_multiple_files=False)
    else:
        # Faz o upload dos arquivos individuais
        uploaded_file = st.file_uploader(f"Choose Files(.txt)", accept_multiple_files=True)

    if uploaded_file is not None:
        result_list = []
        if choice == "Compressed folder(.zip)":
            # Lê o arquivo ZIP em memória
            with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                files = zip_ref.infolist()
                for file_data in files:
                    file_content = zip_ref.read(file_data.filename)

                    # Faz a leitura do arquivo txt
                    df = pd.read_csv(io.BytesIO(file_content), sep="  ", names=['t', 'U', 'I'], usecols=[0, 1, 2], engine='python')
                    df = df.replace({',': '.'}, regex=True).astype(float)

                    if df.shape[0] > 0:
                        # Calcula as estatísticas com base nos dados e armazena os resultados em 'result_list'
                        parameters = calc(df, Ucurto)
                        result_list.append([file_data.filename, parameters["Ief"], parameters["Uef"], parameters["Imed"], parameters["Umed"], parameters["Pmed"], parameters["IVcc"], parameters["tcc"]])        
        else:
            for file_data in uploaded_file:
                # Faz a leitura do arquivo txt
                df = pd.read_csv(file_data, sep="  ", names=['t', 'U', 'I'], usecols=[0, 1, 2], engine='python')
                df = df.replace({',': '.'}, regex=True).astype(float)
                
                if df.shape[0] > 0:
                    # Calcula as estatísticas com base nos dados e armazena os resultados em 'result_list'
                    parameters = calc(df, Ucurto)
                    result_list.append([file_data.name, parameters["Ief"], parameters["Uef"], parameters["Imed"], parameters["Umed"], parameters["Pmed"], parameters["IVcc"], parameters["tcc"]])
        
        # Cria um DataFrame com os resultados e exibe-o
        result_df = pd.DataFrame(result_list, columns=["File", "Ief", "Uef", "Imed", "Umed", "Pmed", "IVcc", "tcc"])
        if result_df.shape[0] > 0:
            st.write(result_df)
            
            # Prepara o DataFrame para download em formato Excel
            data_for_download = convertToExcel(result_df)

            # Cria um botão de download para o arquivo Excel
            st.download_button(
                label="Download data",
                data=data_for_download,
                file_name='data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
if __name__ == "__main__":
    ivc()
