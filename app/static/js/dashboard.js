document.addEventListener('DOMContentLoaded', function() {
    // User chart
    var ctxUsers = document.getElementById('usersChart').getContext('2d');
    var usersChart = new Chart(ctxUsers, {
        type: 'bar',
        data: {
            labels: userLabels,
            datasets: [{
                label: '# of Users',
                data: userCounts,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Issue chart
    var ctxIssues = document.getElementById('issuesChart').getContext('2d');
    var issuesChart = new Chart(ctxIssues, {
        type: 'bar',
        data: {
            labels: issueLabels,
            datasets: [{
                label: '# of Issues',
                data: issueCounts,
                backgroundColor: 'rgba(255, 159, 64, 0.2)',
                borderColor: 'rgba(255, 159, 64, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Order chart
    var ctxOrders = document.getElementById('ordersChart').getContext('2d');
    var ordersChart = new Chart(ctxOrders, {
        type: 'bar',
        data: {
            labels: orderLabels,
            datasets: [{
                label: '# of Orders',
                data: orderCounts,
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
});
