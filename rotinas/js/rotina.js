
document-addEventListener('DOMContentLoaded', (event) => {
        const inputs = document.querySelectorAll('.atividade');

        inputs.forEach((input, index) => {
            input.addEventListener('keydown', (e) => {
                if (e.key == 'Enter') {
                    e.preventDefault();

                    const nextInput = inputs[index + 1];
                    if (nextInput){
                        nextInput.focus();
                    }
                }
            });}
        );
    }
);

document.getElementById('updateButton').addEventListener('click', function() {
        // Seleciona todas as linhas da tabela
        const rows = document.querySelectorAll('table tr');
        const atividades = [];
        
        var registroElement = document.getElementsByClassName('registro');
        
        var registroSelecionado = registroElement[0].selectedIndex;

        var diaSelecionado = registroElement[0].options[registroSelecionado].value;

        atividades.unshift({'dia':diaSelecionado});
        // Itera sobre cada linha
        rows.forEach(row => {
        // Seleciona o elemento <td> com a classe 'hora'
        const horaElement = row.querySelector('.hora');
        // Seleciona o elemento <input> com a classe 'atividade'
        const atividadeElement = row.querySelector('.atividade');
        
        // Verifica se ambos os elementos foram encontrados
        if (horaElement && atividadeElement) {
            // Captura o texto do <td> e o valor do <input>
            const hora = horaElement.innerText;
            const atividade = atividadeElement.value;
            
            // Adiciona os dados ao array
            atividades.push({hora, atividade});
      
        } else {
            console.error('Elemento não encontrado na linha:', row);
        }
        });
        const data = JSON.stringify(atividades)

        fetch ('rotina/form_atividades',{
            method: 'POST',
            
            headers: {
                'Content-Type': 'application/json'
            },
            body: data
        })
        
        .then(response => response.json())
        .then(data => {
        if (data.success) {
            alert('Formulario enviado com sucesso!');
            mensagemDiv.textContent = 'Formulário enviado com sucesso!';
        } else {
            alert('Erro ao enviar formulario: ' + data.message);
            mensagemDiv.textContent = 'Erro ao enviar formulário: ' + data.message;
        }
        })
        .catch((error) => {
            console.error('Error:', error);
        });

});


// document.getElementById('registro').addEventListener('select', function(){
    
//     const registros = document.querySelector('registro');
//     const registros_ext = []


// })