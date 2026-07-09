import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  // This must match your Flask server URL
  // Use localhost host to match the dev server origin and avoid cross-host cookie issues
  private baseUrl = 'http://localhost:5000/api';

  getResultsEndpoint(): string {
    return `${this.baseUrl}/results`;
  }

  // This tells Angular to send the session cookie to Flask so it knows you are logged in
  private httpOptions = {
    withCredentials: true 
  };

  constructor(private http: HttpClient) { }

  // ================= AUTHENTICATION =================
  
  voterLogin(credentials: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/voter/login`, credentials, this.httpOptions);
  }

  voterOtp(otpData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/voter/otp`, otpData, this.httpOptions);
  }

  // ================= ADMIN AUTH =================
  
  adminLogin(credentials: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/admin/login`, credentials, this.httpOptions);
  }

  adminOtp(otpData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/admin/otp`, otpData, this.httpOptions);
  }

  getAuthStatus(): Observable<any> {
    return this.http.get(`${this.baseUrl}/auth/status`, this.httpOptions);
  }

  logout(): Observable<any> {
    return this.http.post(`${this.baseUrl}/logout`, {}, this.httpOptions);
  }

  addCandidate(candidateData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/admin/candidate`, candidateData, this.httpOptions);
  }

  addVoter(voterData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/admin/voter`, voterData, this.httpOptions);
  }

  updateVoter(id: number, voterData: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/admin/voter/${id}`, voterData, this.httpOptions);
  }

  updateCandidate(id: number, candidateData: any): Observable<any> {
    return this.http.put(`${this.baseUrl}/admin/candidate/${id}`, candidateData, this.httpOptions);
  }

  deleteCandidate(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/admin/candidate/${id}`, this.httpOptions);
  }

  deleteVoter(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/admin/voter/${id}`, this.httpOptions);
  }

  // ================= VOTING =================

  getCandidates(): Observable<any> {
    return this.http.get(`${this.baseUrl}/candidates`, this.httpOptions);
  }

  getAdminDashboard(): Observable<any> {
    return this.http.get(`${this.baseUrl}/admin/dashboard`, this.httpOptions);
  }

  resetVotes(): Observable<any> {
    return this.http.post(`${this.baseUrl}/admin/reset_votes`, {}, this.httpOptions);
  }

  getVoter(id: number): Observable<any> {
    return this.http.get(`${this.baseUrl}/admin/voter/${id}`, this.httpOptions);
  }

  getCandidate(id: number): Observable<any> {
    return this.http.get(`${this.baseUrl}/admin/candidate/${id}`, this.httpOptions);
  }

  submitVote(voteData: { candidate_id: number }): Observable<any> {
    return this.http.post(`${this.baseUrl}/vote`, voteData, this.httpOptions);
  }

  // ================= VERIFICATION =================
  
  verify(entity: 'voter' | 'candidate', entityId: number, verifyData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/verify/${entity}/${entityId}`, verifyData, this.httpOptions);
  }

  // ================= RESULTS =================

  getResults(): Observable<any> {
    return this.http.get(this.getResultsEndpoint(), this.httpOptions);
  }
}