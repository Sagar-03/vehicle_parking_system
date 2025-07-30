// Admin Spot Details Modal: Fetch and display real user/vehicle data
document.addEventListener('DOMContentLoaded', function() {
    var spotDetailsModal = document.getElementById('spotDetailsModal');
    if (spotDetailsModal) {
        spotDetailsModal.addEventListener('show.bs.modal', function(event) {
            var button = event.relatedTarget;
            var spotId = button.getAttribute('data-spot-id');
            if (!spotId) return;
            fetch(`/admin/api/spot_details/${spotId}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('modal-spot-id').textContent = data.spot_id || '';
                    document.getElementById('modal-lot-name').textContent = data.parking_lot || '';
                    document.getElementById('modal-spot-number').textContent = data.spot_number || '';
                    document.getElementById('modal-spot-type').textContent = data.spot_type || '';
                    document.getElementById('modal-status').textContent = data.status || '';

                    // User
                    var userRow = document.getElementById('modal-user-row');
                    var userCell = document.getElementById('modal-current-user');
                    if (data.user && data.user.name) {
                        userRow.style.display = '';
                        userCell.textContent = `${data.user.name} (ID: ${data.user.id})`;
                    } else {
                        userRow.style.display = 'none';
                        userCell.textContent = '';
                    }

                    // Vehicle
                    var vehicleRow = document.getElementById('modal-vehicle-row');
                    var vehicleCell = document.getElementById('modal-vehicle');
                    if (data.vehicle && (data.vehicle.model || data.vehicle.license_plate)) {
                        vehicleRow.style.display = '';
                        vehicleCell.textContent = `${data.vehicle.model || ''} (${data.vehicle.license_plate || ''})`;
                    } else {
                        vehicleRow.style.display = 'none';
                        vehicleCell.textContent = '';
                    }

                    // Since
                    var sinceRow = document.getElementById('modal-timestamp-row');
                    var sinceCell = document.getElementById('modal-timestamp');
                    if (data.since) {
                        sinceRow.style.display = '';
                        sinceCell.textContent = data.since;
                    } else {
                        sinceRow.style.display = 'none';
                        sinceCell.textContent = '';
                    }
                })
                .catch(() => {
                    // fallback: clear all fields
                    document.getElementById('modal-spot-id').textContent = '';
                    document.getElementById('modal-lot-name').textContent = '';
                    document.getElementById('modal-spot-number').textContent = '';
                    document.getElementById('modal-spot-type').textContent = '';
                    document.getElementById('modal-status').textContent = '';
                    document.getElementById('modal-user-row').style.display = 'none';
                    document.getElementById('modal-current-user').textContent = '';
                    document.getElementById('modal-vehicle-row').style.display = 'none';
                    document.getElementById('modal-vehicle').textContent = '';
                    document.getElementById('modal-timestamp-row').style.display = 'none';
                    document.getElementById('modal-timestamp').textContent = '';
                });
        });
    }
});
