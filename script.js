const addBtn = document.getElementById("addTask");
const taskList = document.getElementById("taskList");
const emptyMsg = document.getElementById("emptyMsg");
const toggleBtn = document.getElementById("toggleDark");

window.addEventListener("load", () => {
  loadTasks();

  setTimeout(() => {
    const loader = document.getElementById("loader");
    if (loader) loader.style.display = "none";
  }, 1000);
});

addBtn.addEventListener("click", () => {
  const title = document.getElementById("title").value.trim();
  const desc = document.getElementById("desc").value.trim();

  if (!title || !desc) {
    alert("Enter all fields");
    return;
  }

  const task = { title, desc, completed: false };

  saveTask(task);
  displayTask(task);

  document.getElementById("title").value = "";
  document.getElementById("desc").value = "";
});

function saveTask(task) {
  let tasks = JSON.parse(localStorage.getItem("tasks")) || [];
  tasks.push(task);
  localStorage.setItem("tasks", JSON.stringify(tasks));
}

function loadTasks() {
  let tasks = JSON.parse(localStorage.getItem("tasks")) || [];

  if (tasks.length === 0) {
    emptyMsg.style.display = "block";
  } else {
    emptyMsg.style.display = "none";
  }

  tasks.forEach(displayTask);
}

function displayTask(taskObj) {
  emptyMsg.style.display = "none";

  const task = document.createElement("div");
  task.className =
    "bg-white p-4 rounded-lg shadow border-l-4 border-blue-500 fade-in";

  if (taskObj.completed) task.classList.add("completed");

  task.innerHTML = `
    <h3 class="font-bold flex justify-between">
      ${taskObj.title}
      <span class="text-xs px-2 py-1 rounded ${
        taskObj.completed
          ? "bg-green-200 text-green-800"
          : "bg-yellow-200 text-yellow-800"
      }">
        ${taskObj.completed ? "Completed" : "Pending"}
      </span>
    </h3>

    <p>${taskObj.desc}</p>

    <div class="flex justify-between mt-3">
      <button class="done text-green-600 flex items-center gap-1">
        <i class="fa-solid fa-check"></i> Done
      </button>

      <button class="edit text-blue-500 flex items-center gap-1">
        <i class="fa-solid fa-pen"></i> Edit
      </button>

      <button class="delete text-red-500 flex items-center gap-1">
        <i class="fa-solid fa-trash"></i> Delete
      </button>
    </div>
  `;

  const doneBtn = task.querySelector(".done");
  const editBtn = task.querySelector(".edit");
  const deleteBtn = task.querySelector(".delete");

  doneBtn.addEventListener("click", () => {
    taskObj.completed = !taskObj.completed;
    updateStorage();
    location.reload();
  });

  editBtn.addEventListener("click", () => {
    const newTitle = prompt("Edit Title:", taskObj.title);
    const newDesc = prompt("Edit Description:", taskObj.desc);

    if (newTitle && newDesc) {
      taskObj.title = newTitle;
      taskObj.desc = newDesc;
      updateStorage();
      location.reload();
    }
  });

  deleteBtn.addEventListener("click", () => {
    deleteTask(taskObj);
    task.remove();
  });

  taskList.appendChild(task);
}

function updateStorage() {
  const tasks = [];

  document.querySelectorAll("#taskList > div").forEach(task => {
    const title = task.querySelector("h3").childNodes[0].textContent.trim();
    const desc = task.querySelector("p").innerText;
    const completed = task.classList.contains("completed");

    tasks.push({ title, desc, completed });
  });

  localStorage.setItem("tasks", JSON.stringify(tasks));
}

function deleteTask(taskObj) {
  let tasks = JSON.parse(localStorage.getItem("tasks")) || [];

  tasks = tasks.filter(t => t.title !== taskObj.title);

  localStorage.setItem("tasks", JSON.stringify(tasks));
}

function filterTasks(type, btn) {
  document.querySelectorAll(".filter-btn").forEach(b => {
    b.classList.remove("bg-blue-500", "text-white");
  });

  btn.classList.add("bg-blue-500", "text-white");

  let tasks = JSON.parse(localStorage.getItem("tasks")) || [];
  taskList.innerHTML = "";

  if (type === "completed") {
    tasks = tasks.filter(t => t.completed);
  } else if (type === "pending") {
    tasks = tasks.filter(t => !t.completed);
  }

  tasks.forEach(displayTask);
}

toggleBtn.addEventListener("click", () => {
  document.body.classList.toggle("dark");
});