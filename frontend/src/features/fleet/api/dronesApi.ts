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
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.append("page", params.page.toString());
  if (params.pageSize) searchParams.append("page_size", params.pageSize.toString());
  if (params.search) searchParams.append("search", params.search);
  if (params.ordering) searchParams.append("ordering", params.ordering);

  params.status?.forEach(s => searchParams.append("status", s));
  params.classification?.forEach(c => searchParams.append("classification", c));

  const queryString = searchParams.toString();
  const path = queryString ? `drones/?${queryString}` : "drones/";

  return apiRequest<PaginatedResponse<Drone>>(path);
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

  return apiRequest<{
    added_count: number;
    errors: Array<{ row: number | string; error: string }>;
  }>("drones/import/", {
    method: "POST",
    formData,
  });
}
