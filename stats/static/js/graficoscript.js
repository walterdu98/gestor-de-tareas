document.addEventListener('DOMContentLoaded', function() {
    

    const dataElement = document.getElementById('stats-data');
    let completadas = 0;
    let pendientes = 0;
    let no_completadas = 0;

    if (dataElement) {
        const stats = JSON.parse(dataElement.textContent);
        completadas = stats.completadas;
        pendientes = stats.pendientes;
        no_completadas = stats.no_completadas;
    }

    const canvas = document.getElementById('taskChart');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completadas', 'Pendientes', 'No Completadas'],
                datasets: [{
                    data: [completadas, pendientes, no_completadas],
                    backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                plugins: { 
                    legend: { position: 'bottom' } 
                },
                cutout: '70%',
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    const searchInput = document.getElementById('userSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll('.user-row');

            rows.forEach(row => {
                const usernameCell = row.querySelector('.username-cell');
                if (usernameCell) {
                    const username = usernameCell.textContent.toLowerCase();
                    row.style.display = username.includes(filter) ? "" : "none";
                }
            });
        });
    }
});