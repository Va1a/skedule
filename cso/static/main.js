(() => {
  feather.replace({ 'aria-hidden': 'true'})
})()

function updateEndTime(){
  const startTime = document.getElementById('startTime').value
  const startDate = document.getElementById('startDate').value
  const duration = document.getElementById('duration').value
  
  const sHours = parseInt(startTime.slice(0,2));
  const sMins = parseInt(startTime.slice(2));
  const dHours = parseInt(duration.slice(0,2));
  const dMins = parseInt(duration.slice(2));

  
  var date = new Date(startDate);
  date.setTime(date.getTime()+ sHours*60*60*1000 + sMins*60*1000);
  date.setTime(date.getTime()+ dHours*60*60*1000 + dMins*60*1000);
  
  if(date.toString() != 'Invalid Date'){
    document.getElementById('endTime').value = Intl.DateTimeFormat('en-US', {month: '2-digit', day: '2-digit', year: 'numeric', hour:'2-digit', minute:'2-digit', hour12: false}).format(date).split(':').join('');
  } else {
    document.getElementById('endTime').value = '---';
  }
}
updateEndTime()