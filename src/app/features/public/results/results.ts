import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';

export interface Candidate {
  id: number;
  name: string;
  party: string;
  votes: number;
}

export interface Slice {
  name: string;
  votes: number;
  percent: number;
  color: string;
  full_circle?: boolean;
  path?: string;
}

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './results.html',
  styleUrls: ['./results.css']
})
export class ResultsComponent implements OnInit {

  total: number = 0;
  maxVotes: number = 0;
  
  candidates: Candidate[] = [];
  slices: Slice[] = [];

  constructor(private api: ApiService) { }

  ngOnInit(): void {
    this.loadResults();
  }

  loadResults(): void {
    this.api.getResults().subscribe({
      next: res => {
        this.candidates = res.candidates || [];
        this.total = res.total_votes ?? this.candidates.reduce((s, c) => s + (c.votes || 0), 0);
        this.maxVotes = this.candidates.length ? Math.max(...this.candidates.map(c => c.votes || 0)) : 0;

        const colors = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#06B6D4'];
        this.slices = this.candidates.map((c, i) => ({
          name: c.name,
          votes: c.votes || 0,
          percent: this.total > 0 ? Math.round(((c.votes || 0) / this.total) * 1000) / 10 : 0,
          color: colors[i % colors.length]
        }));
      },
      error: err => {
        console.error('Failed to load results', err);
        this.candidates = [];
        this.total = 0;
        this.maxVotes = 0;
        this.slices = [];
      }
    });
  }

}