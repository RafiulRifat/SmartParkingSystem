// =====================================
// SMART PARKING ADMIN PANEL
// STEP 3 - RESERVATION SYSTEM
// =====================================


let parkingChart = null;






// =====================================
// CHECK ADMIN SESSION
// =====================================


function checkSession(data){


    if(data.error === "Unauthorized"){


        window.location.href =
        "/login";


        return false;

    }


    return true;


}









// =====================================
// LOAD SLOT STATUS
// =====================================


async function loadSlotStatus(){


    try{


        const response =

        await fetch("/status");



        const data =

        await response.json();







        updateAdminSlot(

            "admin_slot1",

            data.slot1,

            data.distance1

        );







        updateAdminSlot(

            "admin_slot2",

            data.slot2,

            data.distance2

        );








        if(document.getElementById("admin_available")){


            document.getElementById("admin_available").innerHTML =

            data.available ?? 0;


        }








        if(document.getElementById("admin_distance1")){


            document.getElementById("admin_distance1").innerHTML =

            Number(data.distance1 ?? 0).toFixed(2);


        }








        if(document.getElementById("admin_distance2")){


            document.getElementById("admin_distance2").innerHTML =

            Number(data.distance2 ?? 0).toFixed(2);


        }





    }


    catch(error){


        console.log(

            "Slot Status Error:",

            error

        );


    }


}












// =====================================
// UPDATE ADMIN SLOT
// =====================================


function updateAdminSlot(

    id,

    status,

    distance

){



    const element =

    document.getElementById(id);





    if(!element)

        return;







    if(status === "OCCUPIED"){



        element.innerHTML =

        "🔴 OCCUPIED";



        element.style.color =

        "#ef4444";



    }



    else if(status === "EMPTY"){



        element.innerHTML =

        "🟢 AVAILABLE";



        element.style.color =

        "#22c55e";



    }



    else{


        element.innerHTML =

        "🟡 WAITING";


        element.style.color =

        "#facc15";


    }



}









// =====================================
// LOAD MAIN ADMIN DATA
// =====================================


async function loadAdminData(){


    try{


        const response =

        await fetch("/admin-data");



        const data =

        await response.json();





        if(!checkSession(data))

            return;








        if(document.getElementById("cars_inside")){


            document.getElementById("cars_inside").innerHTML =

            data.inside ?? 0;


        }








        if(document.getElementById("total_entries")){


            document.getElementById("total_entries").innerHTML =

            data.entries ?? 0;


        }








        if(document.getElementById("total_exit")){


            document.getElementById("total_exit").innerHTML =

            data.exit ?? 0;


        }








        if(document.getElementById("total_records")){


            document.getElementById("total_records").innerHTML =

            data.total_records ?? 0;


        }





    }



    catch(error){


        console.log(

            "Admin Data Error:",

            error

        );


    }


}



// =====================================
// LOAD STATISTICS
// =====================================


async function loadStatistics(){


    try{


        const response =

        await fetch("/statistics");



        const data =

        await response.json();





        if(!checkSession(data))

            return;








        if(document.getElementById("today_events")){


            document.getElementById("today_events").innerHTML =

            data.today_events ?? 0;


        }








        if(document.getElementById("daily_entry")){


            document.getElementById("daily_entry").innerHTML =

            data.total_entry ?? 0;


        }








        if(document.getElementById("daily_exit")){


            document.getElementById("daily_exit").innerHTML =

            data.total_exit ?? 0;


        }




    }



    catch(error){


        console.log(

            "Statistics Error:",

            error

        );


    }


}









// =====================================
// LOAD RESERVATIONS
// =====================================


async function loadReservations(){



    try{


        const response =

        await fetch("/reservation-data");



        const data =

        await response.json();






        if(!checkSession(data))

            return;







        const table =

        document.getElementById(

            "reservation_table"

        );





        if(!table)

            return;







        table.innerHTML = "";







        if(data.length === 0){



            table.innerHTML =



            `

            <tr>

            <td colspan="8">

            No Reservations Found

            </td>

            </tr>

            `;



            return;


        }









        data.forEach(

        function(reservation){






            table.innerHTML +=



            `

            <tr>


            <td>

            ${reservation.id}

            </td>



            <td>

            ${reservation.name}

            </td>




            <td>

            ${reservation.phone}

            </td>





            <td>

            ${reservation.slot}

            </td>





            <td>

            ${reservation.date}

            </td>





            <td>

            ${reservation.time}

            </td>





            <td>

            ${reservation.status}

            </td>





            <td>


            <button

            class="admin-btn danger"

            onclick="deleteReservation(${reservation.id})"

            >

            🗑 Delete

            </button>


            </td>





            </tr>

            `;



        }

        );







    }



    catch(error){



        console.log(

            "Reservation Load Error:",

            error

        );



    }



}









// =====================================
// DELETE RESERVATION
// =====================================


async function deleteReservation(id){





    if(!confirm(

        "Delete this reservation?"

    ))

        return;







    try{



        const response =

        await fetch(

        "/delete-reservation",

        {


            method:"POST",



            headers:{


            "Content-Type":

            "application/json"


            },



            body:

            JSON.stringify(

            {

            id:id

            }

            )



        }

        );








        const data =

        await response.json();








        if(!checkSession(data))

            return;







        document.getElementById(

            "message"

        ).innerHTML =



        "✅ " + data.status;








        loadReservations();







    }



    catch(error){



        console.log(

            "Delete Reservation Error:",

            error

        );



    }





}











// =====================================
// LOAD CHART
// =====================================


async function loadChart(){


    try{


        const response =

        await fetch("/chart-data");



        const data =

        await response.json();






        if(!checkSession(data))

            return;







        const canvas =

        document.getElementById(

            "parkingChart"

        );





        if(!canvas)

            return;








        if(parkingChart){


            parkingChart.destroy();


        }








        parkingChart = new Chart(

            canvas,

            {


            type:"line",



            data:{



                labels:data.labels || [],



                datasets:[



                {


                    label:"Entry",


                    data:data.entries || [],


                    borderWidth:3,


                    tension:0.4


                },





                {


                    label:"Exit",


                    data:data.exits || [],


                    borderWidth:3,


                    tension:0.4


                }



                ]



            },





            options:{


                responsive:true,


                plugins:{


                    legend:{


                        labels:{


                            color:"white"


                        }


                    }


                }


            }




        });






    }



    catch(error){


        console.log(

            "Chart Error:",

            error

        );


    }



}


// =====================================
// CLEAR HISTORY
// =====================================


async function clearHistory(){



    if(!confirm(

        "Clear all history records?"

    ))

        return;






    try{


        const response =

        await fetch(

            "/clear-history",

            {


                method:"POST"


            }

        );






        const data =

        await response.json();







        if(!checkSession(data))

            return;








        document.getElementById(

            "message"

        ).innerHTML =



        "✅ " + data.status;








        loadAdminData();

        loadStatistics();

        loadChart();





    }



    catch(error){



        console.log(

            "Clear History Error:",

            error

        );



    }



}











// =====================================
// RESET COUNTER
// =====================================


async function resetCounter(){



    if(!confirm(

        "Reset all counters?"

    ))

        return;








    try{


        const response =

        await fetch(

            "/reset-counter",

            {


                method:"POST"


            }

        );








        const data =

        await response.json();








        if(!checkSession(data))

            return;







        document.getElementById(

            "message"

        ).innerHTML =



        "✅ " + data.status;









        loadAdminData();

        loadStatistics();

        loadSlotStatus();





    }



    catch(error){



        console.log(

            "Reset Counter Error:",

            error

        );



    }



}











// =====================================
// CSV DOWNLOAD
// =====================================


function downloadCSV(){


    window.location.href =

    "/export";


}












// =====================================
// AUTO REFRESH
// =====================================


setInterval(

    loadSlotStatus,

    1000

);






setInterval(

    loadAdminData,

    5000

);







setInterval(

    loadStatistics,

    5000

);







setInterval(

    loadReservations,

    5000

);







setInterval(

    loadChart,

    10000

);











// =====================================
// FIRST LOAD
// =====================================


loadSlotStatus();


loadAdminData();


loadStatistics();


loadReservations();


loadChart();