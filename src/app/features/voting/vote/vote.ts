import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { Router } from '@angular/router';
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
  
  voterName: string = '';
  candidates: Candidate[] = [];

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private api: ApiService
  ) { }

  ngOnInit(): void {
    this.voteForm = this.fb.group({
      selectedCandidateId: ['', Validators.required]
    });

    this.loadVotingData();
  }

  loadVotingData(): void {
    this.api.getCandidates().subscribe({
      next: response => {
        if (response.has_voted) {
          this.router.navigate(['/already-voted']);
          return;
        }

        this.candidates = response.candidates || [];
        this.voterName = response.voter_name || sessionStorage.getItem('voterName') || 'Voter';
      },
      error: error => {
        const msg = error?.error?.error || 'Unable to load ballot information.';
        this.messages = [msg];
      }
    });
  }

  onSubmit(): void {
    if (!this.voteForm.valid) {
      this.messages = ['Please select a candidate before submitting your vote.'];
      return;
    }

    const selectedId = Number(this.voteForm.value.selectedCandidateId);

    this.api.submitVote({ candidate_id: selectedId }).subscribe({
      next: response => {
        this.messages = [response.message || 'Your vote has been successfully cast!'];
        this.router.navigate(['/results']);
      },
      error: error => {
        const msg = error?.error?.error || 'Unable to submit your vote. Please try again.';
        this.messages = [msg];
      }
    });
  }

}