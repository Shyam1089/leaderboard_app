document.addEventListener('DOMContentLoaded', function() {
    // Load users on page load
    loadUsers();
    loadWinners();
    
    // Add event listeners
    document.getElementById('addUserForm').addEventListener('submit', addUser);
    document.getElementById('updateWinnersBtn').addEventListener('click', updateWinners);
    
    // Add event listeners for modals
    const modals = document.querySelectorAll('.modal');
    const modalTriggers = document.querySelectorAll('[data-toggle="modal"]');
    const modalCloses = document.querySelectorAll('.close, .modal-cancel');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const modalId = this.getAttribute('data-target');
            document.querySelector(modalId).style.display = 'block';
        });
    });
    
    modalCloses.forEach(close => {
        close.addEventListener('click', function() {
            const modal = this.closest('.modal');
            modal.style.display = 'none';
        });
    });
    
    window.addEventListener('click', function(event) {
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
        
        // Close popover when clicking outside
        const popover = document.getElementById('userDetailsPopover');
        if (popover.style.display === 'block' && 
            !popover.contains(event.target) && 
            !event.target.classList.contains('user-name')) {
            popover.style.display = 'none';
        }
    });
});

// Load users from API
function loadUsers() {
    fetch('/api/users/')
        .then(response => response.json())
        .then(data => {
            const usersList = document.getElementById('usersList');
            usersList.innerHTML = '';
            
            if (data.results && data.results.length > 0) {
                const userList = document.createElement('ul');
                userList.className = 'user-list';
                
                data.results.forEach(user => {
                    // Create a safe version of the address for the HTML attribute
                    const encodedAddress = encodeURIComponent(user.address);
                    
                    const userItem = document.createElement('li');
                    userItem.className = 'user-item';
                    userItem.innerHTML = `
                        <div class="user-delete" onclick="deleteUser(${user.id})">[X]</div>
                        <div class="user-name" onclick="showUserDetailsPopover(event, '${user.name.replace(/'/g, "\\'")}', ${user.age}, '${encodedAddress}', ${user.points})">${user.name}</div>
                        <div class="user-points">
                            <div class="point-btn point-btn-subtract" onclick="updateUserPoints(${user.id}, -1)">-</div>
                            <span>${user.points}</span>
                            <div class="point-btn point-btn-add" onclick="updateUserPoints(${user.id}, 1)">+</div>
                        </div>
                    `;
                    userList.appendChild(userItem);
                });
                
                usersList.appendChild(userList);
            } else {
                usersList.innerHTML = '<p>No users found.</p>';
            }
        })
        .catch(error => {
            console.error('Error loading users:', error);
            document.getElementById('usersList').innerHTML = '<p>Error loading users. Please try again later.</p>';
        });
}

// Load winners from API
function loadWinners() {
    fetch('/api/winners/')
        .then(response => response.json())
        .then(data => {
            const winnersList = document.getElementById('winnersList');
            winnersList.innerHTML = '';
            
            if (data.results && data.results.length > 0) {
                const table = document.createElement('table');
                table.innerHTML = `
                    <thead>
                        <tr>
                            <th>User</th>
                            <th>Points at Win</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody id="winnersTableBody"></tbody>
                `;
                
                winnersList.appendChild(table);
                const tbody = document.getElementById('winnersTableBody');
                
                // Display winners (API returns them ordered by timestamp, most recent first)
                data.results.forEach(winner => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${winner.user.name}</td>
                        <td>${winner.points_at_win}</td>
                        <td>${new Date(winner.timestamp).toLocaleString()}</td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                winnersList.innerHTML = '<p>No winners found.</p>';
            }
        })
        .catch(error => {
            console.error('Error loading winners:', error);
            document.getElementById('winnersList').innerHTML = '<p>Error loading winners. Please try again later.</p>';
        });
}

// Add a new user
function addUser(event) {
    event.preventDefault();
    
    const name = document.getElementById('userName').value;
    const age = document.getElementById('userAge').value;
    const address = document.getElementById('userAddress').value;
    
    fetch('/api/users/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: name,
            age: parseInt(age),
            address: address,
            points: 0
        }),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('addUserModal').style.display = 'none';
        document.getElementById('addUserForm').reset();
        loadUsers();
    })
    .catch(error => {
        console.error('Error adding user:', error);
        alert('Error adding user. Please try again.');
    });
}

// Delete a user
function deleteUser(userId) {
    if (confirm('Are you sure you want to delete this user?')) {
        fetch(`/api/users/${userId}/`, {
            method: 'DELETE',
        })
        .then(response => {
            if (response.ok) {
                loadUsers();
            } else {
                throw new Error('Failed to delete user');
            }
        })
        .catch(error => {
            console.error('Error deleting user:', error);
            alert('Error deleting user. Please try again.');
        });
    }
}

// Show user details in popover
function showUserDetailsPopover(event, name, age, encodedAddress, points) {
    // Get the popover element
    const popover = document.getElementById('userDetailsPopover');
    
    // Decode the address
    const address = decodeURIComponent(encodedAddress);
    
    // Set the content
    document.getElementById('popoverName').textContent = name;
    document.getElementById('popoverAge').textContent = age;
    document.getElementById('popoverPoints').textContent = points;
    document.getElementById('popoverAddress').textContent = address;
    
    // Position the popover near the clicked element
    const rect = event.target.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    popover.style.left = rect.left + 'px';
    popover.style.top = (rect.bottom + scrollTop + 10) + 'px';
    
    // Show the popover
    popover.style.display = 'block';
    
    // Prevent the event from bubbling up
    event.stopPropagation();
}

// Update user points
function updateUserPoints(userId, change) {
    fetch(`/api/users/${userId}/update_score/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            change: change
        }),
    })
    .then(response => response.json())
    .then(data => {
        loadUsers();
    })
    .catch(error => {
        console.error('Error updating points:', error);
        alert('Error updating points. Please try again.');
    });
}

// Update winners
function updateWinners() {
    fetch('/api/update-winners/', {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`Winner declared: ${data.winner.user.name} with ${data.winner.points_at_win} points!`);
        } else if (data.status === 'tie') {
            alert(data.message);
        }
        loadWinners();
    })
    .catch(error => {
        console.error('Error updating winners:', error);
        alert('Error updating winners. Please try again.');
    });
} 