// =====================================
// SMART PARKING RESERVATION
// =====================================



const form = document.getElementById(
    "reservationForm"
);





// =====================================
// SUBMIT RESERVATION
// =====================================


if(form){


form.addEventListener(

"submit",

async function(e){


e.preventDefault();





const data = {


name:

document.getElementById(

"name"

).value,





phone:

document.getElementById(

"phone"

).value,





slot:

document.getElementById(

"slot"

).value,





date:

document.getElementById(

"date"

).value,





time:

document.getElementById(

"time"

).value



};









try{



const response =

await fetch(

"/reserve-slot",

{


method:"POST",



headers:{


"Content-Type":

"application/json"


},



body:

JSON.stringify(data)



}

);







const result =

await response.json();







const message =

document.getElementById(

"message"

);







if(message){



if(result.status === "success"){



message.innerHTML =

"✅ " + result.message;



}

else{


message.innerHTML =

"⚠️ " + result.message;



}



}









if(result.status==="success"){



form.reset();



}







}



catch(error){



console.log(

"Reservation Error:",

error

);





const message =

document.getElementById(

"message"

);




if(message){


message.innerHTML =

"❌ Server Error";


}




}



}



);

}









// =====================================
// SET MIN DATE TODAY
// =====================================


const dateInput =

document.getElementById(

"date"

);





if(dateInput){



let today =

new Date().toISOString().split("T")[0];



dateInput.min = today;



}