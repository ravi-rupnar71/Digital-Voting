import { Component, OnInit } from '@angular/core';
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
    private api: ApiService
  ) {}

  ngOnInit(): void {
    this.voteForm = this.fb.group({
      selectedCandidateId: ['', Validators.required]
    });
    this.loadCandidates();
  }

  private loadCandidates(): void {
    this.isLoading = true;
    this.hasLoaded = false;
    this.messages  = [];

    this.api.getCandidates().subscribe({
      next: (data: any) => {
        // FIXED: Show a message on the screen instead of trying to navigate to a new page
        if (data?.has_voted) {
          this.messages = ['You have already voted!'];
          this.candidates = [];
          this.hasLoaded = true;
          this.isLoading = false;
          return;
        }

        this.candidates = Array.isArray(data) ? data : (data?.candidates || []);
        this.voterName = data?.voter_name || sessionStorage.getItem('voterName') || 'Voter';

        this.hasLoaded = true;
        this.isLoading = false;
        this.retryCount = 0;
      },
      error: (error: any) => {
        console.error('Error loading candidates:', error);

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
      next: response => {
        this.router.navigate(['/results']);
      },
      error: error => {
        const msg = error?.error?.error || 'Unable to submit vote. Please try again.';
        this.messages = [msg];

        if (error?.status === 401) {
          this.router.navigate(['/voter-login']);
        }
        
        // FIXED: Show a message if they already voted mid-session
        if (error?.status === 403) {
          this.messages = ['You have already voted!'];
          this.candidates = [];
        }
      }
    });
  }

  resetVote(): void {
    this.voteForm.reset();
    this.messages = [];
  }

}