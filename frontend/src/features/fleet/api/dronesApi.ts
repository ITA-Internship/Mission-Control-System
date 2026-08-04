import type { Drone, PaginatedResponse, DroneModel, MilitaryUnit } from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export async function fetchDrones(params: {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: string[];
  classification?: string[];
  ordering?: string;
}) {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.append("page", params.page.toString());
  if (params.search) queryParams.append("search", params.search);

  if (params.status?.length) {
    params.status.forEach(s => queryParams.append("status", s));
  }
  if (params.classification?.length) {
    params.classification.forEach(c => queryParams.append("classification", c));
  }
  if (params.ordering) {
    queryParams.append("ordering", params.ordering);
  }

  const response = await fetch(`${API_URL}/drones/?${queryParams.toString()}`, {
    method: "GET",
    credentials: "include",
    headers: {
      "Accept": "application/json",
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json() as Promise<PaginatedResponse<Drone>>;
}

function getCookie(name: string): string | null {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export async function fetchDroneModels() {
  const response = await fetch(`${API_URL}/drones/models/`, {
    method: "GET",
    credentials: "include",
    headers: {
      "Accept": "application/json",
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json() as Promise<PaginatedResponse<DroneModel>>;
}

export async function fetchMilitaryUnits() {
  const response = await fetch(`${API_URL}/military-units/`, {
    method: "GET",
    credentials: "include",
    headers: {
      "Accept": "application/json",
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json() as Promise<PaginatedResponse<MilitaryUnit>>;
}

export async function createDrone(data: any) {
  const csrfToken = getCookie("csrftoken"); // Дістаємо токен

  const response = await fetch(`${API_URL}/drones/`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken || "", // Передаємо бекенду
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(JSON.stringify(error));
  }

  return response.json() as Promise<Drone>;
}

export async function updateDrone(id: number, data: any) {
  const csrfToken = getCookie("csrftoken"); // Дістаємо токен

  const response = await fetch(`${API_URL}/drones/${id}/`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken || "", // Передаємо бекенду
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(JSON.stringify(error));
  }

  return response.json() as Promise<Drone>;
}

export async function importDronesCSV(file: File) {
  const csrfToken = getCookie("csrftoken");
  const formData = new FormData();

  // Ключ "file" має збігатися з тим, що очікує DroneImportSerializer
  formData.append("file", file);

  // ПЕРЕВІР URL: Залежно від твого urls.py, це може бути /drones/import/ або просто /import/
  const response = await fetch(`${API_URL}/drones/import/`, {
    method: "POST",
    credentials: "include",
    headers: {
      "Accept": "application/json",
      "X-CSRFToken": csrfToken || "",
    },
    body: formData, // Передаємо FormData напряму, без JSON.stringify
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    // Витягуємо текст помилки, якщо він є у форматі бекенду
    throw new Error(errorData.error || errorData.file?.[0] || "Failed to import file");
  }

  return response.json();
}