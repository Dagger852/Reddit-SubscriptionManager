const userSubreddits = [];
let redditName = localStorage.getItem("redditName");
document.getElementById("redditName").textContent = redditName;
let userSubredditsData = localStorage.getItem("userSubreddits");
if (userSubredditsData) {
    userSubredditsData = JSON.parse(userSubredditsData);
    for (let i = 0; i < userSubredditsData.length; i++) {
        let row = document.createElement("tr");
        let nameCell = document.createElement("td");
        nameCell.textContent = userSubredditsData[i].name;
        let typeCell = document.createElement("td");
        typeCell.textContent = userSubredditsData[i].type;
        let rankCell = document.createElement("td");
        rankCell.textContent = userSubredditsData[i].rank;
        let vipCell = document.createElement("td");
        vipCell.textContent = userSubredditsData[i].vip;
        let freeCell = document.createElement("td");
        freeCell.textContent = userSubredditsData[i].free;
        let rrCell = document.createElement("td");
        rrCell.textContent = userSubredditsData[i].rr;
        let ppCell = document.createElement("td");
        ppCell.textContent = userSubredditsData[i].pp;
        let altAcct1Cell = document.createElement("td");
        altAcct1Cell.textContent = userSubredditsData[i].altAcct1;
        let altAcct2Cell = document.createElement("td");
        altAcct2Cell.textContent = userSubredditsData[i].altAcct2;
        let deletedCell = document.createElement("td");
        deletedCell.textContent = userSubredditsData[i].deleted;
        let tagsCell = document.createElement("td");
        tagsCell.textContent = userSubredditsData[i].tags;
        let otherCell = document.createElement("td");
        otherCell.textContent = userSubredditsData[i].other;

        row.appendChild(nameCell);
        row.appendChild(typeCell);
        row.appendChild(rankCell);
        row.appendChild(vipCell);
        row.appendChild(freeCell);
        row.appendChild(rrCell);
        row.appendChild(ppCell);
        row.appendChild(altAcct1Cell);
        row.appendChild(altAcct2Cell);
        row.appendChild(deletedCell);
        row.appendChild(tagsCell);
        row.appendChild(otherCell);

        if (userSubredditsData[i].deleted === "true") {
            let deletedRow = document.createElement("tr");
            let deletedNameCell = document.createElement("td");
            deletedNameCell.textContent = userSubredditsData[i].name;
            deletedRow.appendChild(deletedNameCell);
            document.getElementById("deletedEntriesTable").appendChild(deletedRow);
        } else {
            document.getElementById("subredditsTable").appendChild(row);
        }
    }
}

document.getElementById("exportCsvBtn").addEventListener("click", function () {
    exportAsCsv(userSubredditsData);
});

document.getElementById("exportJsonBtn").addEventListener("click", function () {
    exportAsJson(userSubredditsData);
});

document.getElementById("darkModeSwitch").addEventListener("change", function () {
    document.body.classList.toggle("dark-mode");
});

document.getElementById("addSubredditBtn").addEventListener("click", function () {
    const subredditName = document.getElementById("subredditName").value;
    addSubreddit(subredditName);
});

document.getElementById("clearEntriesBtn").addEventListener("click", function () {
    if (confirm("Are you sure you want to clear all entries?")) {
        localStorage.removeItem("userSubreddits");
        document.getElementById("subredditsTable").innerHTML = "";
        document.getElementById("deletedEntriesTable").innerHTML = "";
        console.log("All entries cleared.");
    }
});

function openNav() {
    document.getElementById("mySidebar").style.width = "250px";
    document.getElementById("sidebarCollapseBtn").style.display = "none";
    document.body.classList.add("sidebar-open");
}

function closeNav() {
    document.getElementById("mySidebar").style.width = "0";
    document.getElementById("sidebarCollapseBtn").style.display = "block";
    document.body.classList.remove("sidebar-open");
}

function exportAsCsv(subreddits) {
    let csvContent = "data:text/csv;charset=utf-8,Name,Type,Rank,VIP,Free,RR,PP,Alt Acct 1,Alt Acct 2,Deleted,Tags,Other\n";
    for (let i = 0; i < subreddits.length; i++) {
        let row = `${subreddits[i].name},${subreddits[i].type},${subreddits[i].rank},${subreddits[i].vip},${subreddits[i].free},${subreddits[i].rr},${subreddits[i].pp},${subreddits[i].altAcct1},${subreddits[i].altAcct2},${subreddits[i].deleted},${subreddits[i].tags},${subreddits[i].other}\n`;
        csvContent += row;
    }
    let encodedUri = encodeURI(csvContent);
    let link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "subreddits.csv");
    document.body.appendChild(link);
    link.click();
}

function exportAsJson(subreddits) {
    let jsonContent = JSON.stringify(subreddits);
    let encodedUri = encodeURI("data:text/json;charset=utf-8," + jsonContent);
    let link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "subreddits.json");
    document.body.appendChild(link);
    link.click();
}

function addSubreddit(subredditName) {
    const existingSubreddit = Array.from(document.querySelectorAll("#subredditsTable tbody tr")).find((row) => row.cells[0].textContent === subredditName);

    if (existingSubreddit) {
        alert("Subreddit already exists in the table!");
        return;
    }

    // Create a modal or form to prompt for additional information
    const modal = document.createElement("div");
    modal.classList.add("modal");
                    
    document.body.appendChild(modal);
        const additionalInfoForm = document.getElementById("additionalInfoForm");
    
    additionalInfoForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const type = this.elements.type.value;
        const rank = this.elements.rank.value;
        const vip = this.elements.vip.checked;
        const free = this.elements.free.checked;
        const rr = this.elements.rr.checked;
        const pp = this.elements.pp.checked;
        const altAcct1 = this.elements.altAcct1.value;
        const altAcct2 = this.elements.altAcct2.value;
        const deleted = this.elements.deleted.checked;
        const tags = this.elements.tags.value;
        const other = this.elements.other.value;

        const newRow = document.createElement("tr");
        const nameCell = document.createElement("td");
        nameCell.textContent = subredditName;
        const typeCell = document.createElement("td");
        typeCell.textContent = type;
        const rankCell = document.createElement("td");
        rankCell.textContent = rank;
        const vipCell = document.createElement("td");
        vipCell.textContent = vip ? "Yes" : "No";
        const freeCell = document.createElement("td");
        freeCell.textContent = free ? "Yes" : "No";
        const rrCell = document.createElement("td");
        rrCell.textContent = rr ? "Yes" : "No";
        const ppCell = document.createElement("td");
        ppCell.textContent = pp ? "Yes" : "No";
        const altAcct1Cell = document.createElement("td");
        altAcct1Cell.textContent = altAcct1;
        const altAcct2Cell = document.createElement("td");
        altAcct2Cell.textContent = altAcct2;
        const deletedCell = document.createElement("td");
        deletedCell.textContent = deleted ? "Yes" : "No";
        const tagsCell = document.createElement("td");
        tagsCell.textContent = tags;
        const otherCell = document.createElement("td");
        otherCell.textContent = other;

        newRow.appendChild(nameCell);
        newRow.appendChild(typeCell);
        newRow.appendChild(rankCell);
        newRow.appendChild(vipCell);
        newRow.appendChild(freeCell);
        newRow.appendChild(rrCell);
        newRow.appendChild(ppCell);
        newRow.appendChild(altAcct1Cell);
        newRow.appendChild(altAcct2Cell);
        newRow.appendChild(deletedCell);
        newRow.appendChild(tagsCell);
        newRow.appendChild(otherCell);

        if (deleted) {
            document.getElementById("deletedEntriesTable").appendChild(newRow);
        } else {
            document.querySelector("#subredditsTable tbody").appendChild(newRow);
        }

        let userSubredditsData = JSON.parse(localStorage.getItem("userSubreddits")) || [];
        let deletedEntries = JSON.parse(localStorage.getItem("deletedEntries")) || [];

        if (deleted) {
            deletedEntries.push({
                name: subredditName,
                type: type,
                rank: rank,
                vip: vip,
                free: free,
                rr: rr,
                pp: pp,
                altAcct1: altAcct1,
                altAcct2: altAcct2,
                tags: tags,
                other: other
            });
            localStorage.setItem("deletedEntries", JSON.stringify(deletedEntries));
        } else {
            userSubredditsData.push({
                name: subredditName,
                type: type,
                rank: rank,
                vip: vip,
                free: free,
                rr: rr,
                pp: pp,
                altAcct1: altAcct1,
                altAcct2: altAcct2,
                deleted: deleted,
                tags: tags,
                other: other
            });
            localStorage.setItem("userSubreddits", JSON.stringify(userSubredditsData));

            // Append the new row to the subreddits table
            document.querySelector("#subredditsTable tbody").appendChild(newRow);
        }

        // Write to database (assuming you have a function to handle this)
        writeToDatabase(userSubredditsData);

        modal.remove();
    });

    document.getElementById("cancelBtn").addEventListener("click", function () {
        modal.remove();
    });

    modal.style.display = "block";
}

// Sorting functionality
$(".sortable").click(function () {
    var table = $(this).parents("table").eq(0);
    var rows = table
        .find("tr:gt(0)")
        .toArray()
        .sort(comparer($(this).index()));
    this.asc = !this.asc;
    if (!this.asc) {
        rows = rows.reverse();
    }
    table.children("tbody").empty().html(rows);
});

function comparer(index) {
    return function (a, b) {
        var valA = getCellValue(a, index),
            valB = getCellValue(b, index);
        return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.localeCompare(valB);
    };
}

function getCellValue(row, index) {
    return $(row).children("td").eq(index).text();
}

// Pagination
var rowsPerPage = 10;
var rows = $("#subredditsTable tr");
var numPages = Math.ceil(rows.length / rowsPerPage);
var currentPage = 1;

function showPage(page) {
    var startIndex = (page - 1) * rowsPerPage;
    var endIndex = startIndex + rowsPerPage;

    rows.hide();
    rows.slice(startIndex, endIndex).show();

    $("#paginationNav li").removeClass("active");
    $("#paginationNav li:eq(" + (page - 1) + ")").addClass("active");
}

function updatePagination() {
    $("#paginationNav").empty();
    numPages = Math.ceil(rows.filter(":visible").length / rowsPerPage);

    for (var i = 0; i < numPages; i++) {
        var pageNum = i + 1;
        $("#paginationNav").append('<li class="page-item"><a class="page-link" href="#">' + pageNum + "</a></li>");
    }

    $("#paginationNav li:first-child").addClass("active");

    $("#paginationNav li").click(function () {
        currentPage = parseInt($(this).text());
        showPage(currentPage);
    });
}

updatePagination();
showPage(currentPage);

// Filtering/Searching
function filterTable() {
    var filterValue = $("#searchInput").val().toLowerCase();

    rows.filter(function () {
        var rowText = $(this).text().toLowerCase();
        return rowText.indexOf(filterValue) === -1;
    }).hide();

    rows.filter(function () {
        var rowText = $(this).text().toLowerCase();
        return rowText.indexOf(filterValue) !== -1;
    }).show();

    updatePagination();
    showPage(1);
}

$("#filterBtn").click(filterTable);
$("#searchInput").keyup(filterTable);

$("#resetBtn").click(function () {
    $("#searchInput").val("");
    rows.show();
    updatePagination();
    showPage(1);
});

// Close the sidebar by default
closeNav();

document.getElementById("addSubredditBtn").addEventListener("click", function () {
    $('#addSubredditModal').modal('show');
});

document.getElementById("additionalInfoForm").addEventListener("submit", function (event) {
    event.preventDefault();

    const subredditName = document.getElementById("subredditName").value;
    const type = document.getElementById("type").value;
    const rank = document.getElementById("rank").value;
    const vip = document.getElementById("vip").checked;
    const free = document.getElementById("free").checked;
    const rr = document.getElementById("rr").checked;
    const pp = document.getElementById("pp").checked;
    const altAcct1 = document.getElementById("altAcct1").value;
    const altAcct2 = document.getElementById("altAcct2").value;
    const deleted = document.getElementById("deleted").checked;
    const tags = document.getElementById("tags").value;
    const other = document.getElementById("other").value;

    const newRow = document.createElement("tr");
    newRow.innerHTML = `
        <td>${subredditName}</td>
        <td>${type}</td>
        <td>${rank}</td>
        <td>${vip ? "Yes" : "No"}</td>
        <td>${free ? "Yes" : "No"}</td>
        <td>${rr ? "Yes" : "No"}</td>
        <td>${pp ? "Yes" : "No"}</td>
        <td>${altAcct1}</td>
        <td>${altAcct2}</td>
        <td>${deleted ? "Yes" : "No"}</td>
        <td>${tags}</td>
        <td>${other}</td>
    `;

    if (deleted) {
        document.getElementById("deletedEntriesTable").appendChild(newRow);
    } else {
        document.querySelector("#myTable tbody").appendChild(newRow);
    }

    let userSubredditsData = JSON.parse(localStorage.getItem("userSubreddits")) || [];
    let deletedEntries = JSON.parse(localStorage.getItem("deletedEntries")) || [];

    if (deleted) {
        deletedEntries.push({
            name: subredditName,
            type: type,
            rank: rank,
            vip: vip,
            free: free,
            rr: rr,
            pp: pp,
            altAcct1: altAcct1,
            altAcct2: altAcct2,
            tags: tags,
            other: other
        });
        localStorage.setItem("deletedEntries", JSON.stringify(deletedEntries));
    } else {
        userSubredditsData.push({
            name: subredditName,
            type: type,
            rank: rank,
            vip: vip,
            free: free,
            rr: rr,
            pp: pp,
            altAcct1: altAcct1,
            altAcct2: altAcct2,
            deleted: deleted,
            tags: tags,
            other: other
        });
        localStorage.setItem("userSubreddits", JSON.stringify(userSubredditsData));
    }

    $('#addSubredditModal').modal('hide');
    this.reset();
});