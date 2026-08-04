import { apiRequest } from "../../../shared/api/apiClient";
import type { Drone, PaginatedResponse, DroneModel, MilitaryUnit } from "../types";

export async function fetchDrones(params: {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: string[];
  classification?: string[];
  ordering?: string;
} = {}) {
  const queryParams = new URLSearchParams();

  if (params.page) queryParams.append("page", params.page.toString());
  if (params.pageSize) queryParams.append("page_size", params.pageSize.toString());
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

  return apiRequest<PaginatedResponse<Drone>>(`drones/?${queryParams.toString()}`);
}

export async function fetchDroneModels() {
  return apiRequest<PaginatedResponse<DroneModel>>("drones/models/");
}

export async function fetchMilitaryUnits() {
  return apiRequest<PaginatedResponse<MilitaryUnit>>("military-units/");
}

export async function createDrone(data: Partial<Drone>) {
  return apiRequest<Drone>("drones/", {
    method: "POST",
    json: data,
  });
}

export async function updateDrone(id: number | string, data: Partial<Drone>) {
  return apiRequest<Drone>(`drones/${id}/`, {
    method: "PATCH",
    json: data,
  });
}

export async function importDronesCSV(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<{ added_count: number; errors: any[] }>("drones/import/", {
    method: "POST",
    formData,
  });
}
