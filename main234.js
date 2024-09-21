const slider = document.querySelector('.slider');
const slides = document.querySelectorAll('.slide');
const prevBtn = document.querySelector('.prev');
const nextBtn = document.querySelector('.next');
let currentSlide = 0;

function goToSlide(index) {
    slider.style.transform = `translateX(-${index * 100}%)`;
    currentSlide = index;
}

prevBtn.addEventListener('click', () => {
    goToSlide((currentSlide - 1 + slides.length) % slides.length);
});

nextBtn.addEventListener('click', () => {
    goToSlide((currentSlide + 1) % slides.length);
});

// Initially show the first slide
goToSlide(0);