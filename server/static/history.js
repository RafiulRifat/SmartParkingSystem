// =====================================
// SMART PARKING HISTORY
// Flask -> SQLite -> History Page
// =====================================


let historyData = [];




// =====================================
// LOAD HISTORY DATA
// =====================================

async function loadHistory(){


    try{


        const response =
        await fetch("/history-data");



        historyData =
        await response.json();





        const table =
        document.querySelector(
            "#historyTable tbody"
        );



        if(!table)
            return;




        table.innerHTML = "";







        historyData.forEach(row=>{



            table.innerHTML += `


            <tr>


                <td>
                    ${row.id ?? 0}
                </td>



                <td>
                    ${row.time ?? "--"}
                </td>



                <td>
                    ${row.slot1 ?? "EMPTY"}
                </td>



                <td>
                    ${row.slot2 ?? "EMPTY"}
                </td>



                <td>
                    ${row.cars_inside ?? 0}
                </td>



                <td>
                    ${row.total_entries ?? 0}
                </td>



                <td>
                    ${row.total_exit ?? 0}
                </td>


            </tr>


            `;



        });








        const count =
        document.getElementById(
            "recordCount"
        );



        if(count){


            count.innerHTML =
            historyData.length;


        }







        console.log(
            "History Updated:",
            historyData
        );



    }



    catch(error){



        console.log(
            "History Load Error:",
            error
        );



    }



}









// =====================================
// EXPORT CSV
// =====================================


function exportCSV(){



    if(historyData.length === 0){


        alert(
            "No history data available"
        );


        return;


    }







    let csv =

    "ID,Time,Slot1,Slot2,Cars Inside,Entry,Exit\n";







    historyData.forEach(row=>{



        csv +=

        `${row.id ?? 0},` +
        `${row.time ?? ""},` +
        `${row.slot1 ?? ""},` +
        `${row.slot2 ?? ""},` +
        `${row.cars_inside ?? 0},` +
        `${row.total_entries ?? 0},` +
        `${row.total_exit ?? 0}\n`;



    });








    const blob =

    new Blob(

        [csv],

        {
            type:"text/csv"
        }

    );








    const url =

    URL.createObjectURL(blob);







    const link =

    document.createElement("a");





    link.href = url;


    link.download =

    "parking_history.csv";





    link.click();





    URL.revokeObjectURL(url);



}









// =====================================
// AUTO REFRESH
// =====================================


setInterval(

    loadHistory,

    2000

);









// =====================================
// FIRST LOAD
// =====================================


loadHistory();