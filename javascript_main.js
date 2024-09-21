// Get references to HTML elements
const addHabitForm = document.getElementById('add-habit-form');
const updateHabitForm = document.getElementById('update-habit-form');
const analyzeRoutineForm = document.getElementById('analyze-routine-form');
const getRagInsightsButton = document.getElementById('get-rag-insights-button');
const getChartsButton = document.getElementById('get-charts-button');
const habitList = document.getElementById('habit-list');

// Add event listeners to HTML elements
addHabitForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const habit = document.getElementById('habit-input').value;
  const frequency = document.getElementById('frequency-input').value;

  // Validate user input
  if (habit === '' || frequency === '') {
    alert('Please fill in all fields');
    return;
  }

  // Send request to Flask backend
  fetch('/add_habit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ habit, frequency })
  })
  .then(response => response.json())
  .then(data => {
    // Process data returned from Flask backend
    const habitData = data.result;
    const habitHTML = `
      <li>
        <span>${habitData.habit}</span>
        <span>${habitData.frequency}</span>
      </li>
    `;
    habitList.innerHTML += habitHTML;
  })
  .catch(error => {
    console.error('Error adding habit:', error);
  });
});

updateHabitForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const habit = document.getElementById('habit-input').value;
  const completed = document.getElementById('completed-input').checked;

  // Validate user input
  if (habit === '') {
    alert('Please fill in the habit field');
    return;
  }

  // Send request to Flask backend
  fetch('/update_habit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ habit, completed })
  })
  .then(response => response.json())
  .then(data => {
    // Process data returned from Flask backend
    const habitData = data.result;
    const habitHTML = `
      <li>
        <span>${habitData.habit}</span>
        <span>${habitData.completed ? 'Completed' : 'Not Completed'}</span>
      </li>
    `;
    habitList.innerHTML += habitHTML;
  })
  .catch(error => {
    console.error('Error updating habit:', error);
  });
});

analyzeRoutineForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const routine = document.getElementById('routine-input').value;

  // Validate user input
  if (routine === '') {
    alert('Please fill in the routine field');
    return;
  }

  // Send request to Flask backend
  fetch('/analyze_routine', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ routine })
  })
  .then(response => response.json())
  .then(data => {
    // Process data returned from Flask backend
    const analysisData = data.brief_analysis;
    const analysisHTML = `
      <p>${analysisData}</p>
    `;
    document.getElementById('analysis-output').innerHTML = analysisHTML;
  })
  .catch(error => {
    console.error('Error analyzing routine:', error);
  });
});

getRagInsightsButton.addEventListener('click', () => {
  // Send request to Flask backend
  fetch('/get_rag_insights')
  .then(response => response.json())
  .then(data => {
    // Process data returned from Flask backend
    const ragInsightsData = data.rag_insights;
    const ragInsightsHTML = `
      <p>${ragInsightsData}</p>
    `;
    document.getElementById('rag-insights-output').innerHTML = ragInsightsHTML;
  })
  .catch(error => {
    console.error('Error getting RAG insights:', error);
  });
});

getChartsButton.addEventListener('click', () => {
  // Send request to Flask backend
  fetch('/get_charts')
  .then(response => response.json())
  .then(data => {
    // Process data returned from Flask backend
    const habitChartData = data.habit_chart;
    const routineChartData = data.routine_chart;
    const chartHTML = `
      <div>
        <h2>Habit Chart</h2>
        <p>${habitChartData}</p>
      </div>
      <div>
        <h2>Routine Chart</h2>
        <p>${routineChartData}</p>
      </div>
    `;
    document.getElementById('chart-output').innerHTML = chartHTML;
  })
  .catch(error => {
    console.error('Error getting charts:', error);
  });
});