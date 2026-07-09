import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { ApiService } from '../../../core/services/api';

export interface Candidate {
  id: number;
  name: string;
  party: string;
}

@Component({
  selector: 'app-vote',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './vote.html',
  styleUrls: ['./vote.css']
})
export class VoteComponent implements OnInit {

  voteForm!: FormGroup;
  messages: string[] = [];
  isLoading  = true;
  hasLoaded  = false;
  retryCount = 0;
  maxRetries = 2;

  voterName  = '';
  candidates: Candidate[] = [];

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.voteForm = this.fb.group({
      selectedCandidateId: ['', Validators.required]
    });
    this.loadVoterIdentity();
    this.loadCandidates();
  }

  private loadVoterIdentity(): void {
    this.api.getAuthStatus().subscribe({
      next: (status: any) => {
        const sessionName = status?.voter_name || status?.name || '';
        if (sessionName) {
          this.voterName = sessionName;
          sessionStorage.setItem('voterName', sessionName);
        } else {
          this.voterName = sessionStorage.getItem('voterName') || 'Voter';
        }
      },
      error: () => {
        this.voterName = sessionStorage.getItem('voterName') || 'Voter';
      }
    });
  }

  private loadCandidates(): void {
    this.isLoading = true;
    this.hasLoaded = false;
    this.messages  = [];

    this.api.getCandidates().subscribe({
      next: (data: any) => {
        if (data?.has_voted) {
          this.messages = ['You have already voted!'];
          this.candidates = [];
          this.hasLoaded = true;
          this.isLoading = false;
          this.cdr.detectChanges();
          return;
        }

        this.candidates = Array.isArray(data) ? data : (data?.candidates || []);
        if (!this.voterName) {
          this.voterName = data?.voter_name || sessionStorage.getItem('voterName') || 'Voter';
        }

        this.hasLoaded = true;
        this.isLoading = false;
        this.retryCount = 0;
        
        this.cdr.detectChanges();
      },
      error: (error: any) => {
        console.error('❌ ERROR LOADING CANDIDATES:', error);

        if (error?.status === 401) {
          this.router.navigate(['/voter-login']);
          return;
        }

        if (this.retryCount < this.maxRetries) {
          this.retryCount++;
          setTimeout(() => this.loadCandidates(), 1000 * this.retryCount);
          return;
        }

        this.messages = [error?.error?.error || error?.message || 'Unable to load ballot. Please refresh or login again.'];
        this.candidates = [];
        this.hasLoaded  = true;
        this.isLoading  = false;
        this.cdr.detectChanges();
      }
    });
  }

  onSubmit(): void {
    if (!this.voteForm.valid) {
      this.messages = ['Please select a candidate before submitting.'];
      return;
    }

    const selectedId = Number(this.voteForm.value.selectedCandidateId);

    this.api.submitVote({ candidate_id: selectedId }).subscribe({
      next: () => {
        this.router.navigate(['/already-voted']);
      },
      error: error => {
        const msg = error?.error?.error || 'Unable to submit vote. Please try again.';
        this.messages = [msg];

        if (error?.status === 401) {
          this.router.navigate(['/voter-login']);
        }
        
        if (error?.status === 403) {
          this.messages = ['You have already voted!'];
          this.candidates = [];
          this.cdr.detectChanges();
        }
      }
    });
  }
}