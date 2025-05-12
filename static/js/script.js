window.onload = function () {
    setTimeout(function () {
      let alerts = document.querySelectorAll('.alert');
      alerts.forEach(function (alert) {
        alert.style.display = 'none';
      });
    }, 5000); 
  };
  