// static/js/script.js

const form = document.getElementById('form');

const loader = document.getElementById('loader');

const fileInput = document.getElementById('fileInput');

const resultContainer = document.getElementById('resultContainer');

const progressContainer = document.getElementById('progressContainer');

const progressBar = document.getElementById('progressBar');

const toast = document.getElementById('toast');

const fileInfo = document.getElementById('fileInfo');

const formatSelect = document.getElementById('formatSelect');

const bgButtons = document.querySelectorAll('.bg-btn');

const bgInput = document.getElementById('bgInput');

let selectedBg = "transparent";


// =======================
// File Info
// =======================

fileInput.addEventListener('change', () => {

    const files = fileInput.files;

    if(files.length){

        fileInfo.innerHTML = `
            📄 ${files.length} file(s) selected
        `;
    }

});


// =======================
// Form Submit
// =======================

form.addEventListener('submit', async (e) => {

    e.preventDefault();

    const files = fileInput.files;

    if (!files.length) {

        alert("Please select images");

        return;
    }

    // Reset
    resultContainer.innerHTML = "";

    resultContainer.style.display = 'none';

    loader.style.display = 'block';

    progressContainer.style.display = 'block';

    progressBar.style.width = '0%';

    let progress = 0;

    const interval = setInterval(() => {

        progress += 10;

        progressBar.style.width = progress + '%';

        if(progress >= 90){

            clearInterval(interval);

        }

    }, 200);

    try {

        for(let file of files){

            const data = new FormData();

            data.append('image', file);

            const response = await fetch('/remove-bg', {

                method: 'POST',

                body: data

            });

            const out = await response.json();

            console.log(out);

            if(out.image){

                const card = document.createElement('div');

                card.classList.add('box');

                card.innerHTML = `

                    <h3>${file.name}</h3>

                    <img src="${out.image}" class="result-img">

                    <a href="${out.image}" download="${file.name}.${formatSelect.value}">

                        <button>Download</button>

                    </a>

                `;

                resultContainer.appendChild(card);

                // SHOW RESULT
                resultContainer.style.display = 'flex';

            }

            else{

                alert(out.error || "Background removal failed");

            }

        }

        loader.style.display = 'none';

        progressBar.style.width = '100%';

        // Toast
        toast.classList.add('show');

        setTimeout(() => {

            toast.classList.remove('show');

        }, 3000);

    }

    catch(error){

        console.error(error);

        loader.style.display = 'none';

        progressContainer.style.display = 'none';

        progressBar.style.width = '0%';

        alert("Server Error");

    }

});


// =======================
// Background Colors
// =======================

bgButtons.forEach((btn) => {

    btn.addEventListener('click', () => {

        selectedBg = btn.dataset.color;

        document.querySelectorAll('.result-img').forEach((img) => {

            img.style.background = selectedBg;

        });

    });

});


// =======================
// Custom Background
// =======================

bgInput.addEventListener('change', () => {

    const file = bgInput.files[0];

    if(!file) return;

    const bgURL = URL.createObjectURL(file);

    document.querySelectorAll('.result-img').forEach((img) => {

        img.style.background = `url(${bgURL})`;

        img.style.backgroundSize = "cover";

        img.style.backgroundPosition = "center";

    });

});