import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

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

  constructor() {}

  ngOnInit(): void {
    this.loadAndDisplayResults();
  }

  async loadAndDisplayResults() {
    try {
      console.log('Fetching results with fetch()...');
      const response = await fetch('http://localhost:5000/api/results');
      const res = await response.json();
      console.log('Fetch response:', res);
      
      if (!res) return;
      
      this.candidates = res.candidates || [];
      this.total = res.total_votes || this.candidates.reduce((s: any, c: any) => s + (c.votes || 0), 0);
      this.maxVotes = this.candidates.length > 0 ? Math.max(...this.candidates.map((c: any) => c.votes || 0)) : 0;
      
      console.log('Set total to:', this.total);
      console.log('Set candidates to:', this.candidates);

      const colors = ['#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];
      this.slices = this.generatePieSlices(this.candidates, colors);
      
      console.log('Results loaded successfully. Total:', this.total);
    } catch (error) {
      console.error('Error loading results:', error);
    }
  }

  private generatePieSlices(candidates: Candidate[], colors: string[]): Slice[] {
    if (this.total === 0) return [];

    let currentAngle = -90;
    const radius = 90;
    const centerX = 100;
    const centerY = 100;

    return candidates.map((c, i) => {
      const votes = c.votes || 0;
      const percent = this.total > 0 ? Math.round((votes / this.total) * 1000) / 10 : 0;
      const sliceAngle = (votes / this.total) * 360;
      const full_circle = sliceAngle >= 359.9;

      let path = '';
      if (!full_circle) {
        const startAngleRad = (currentAngle * Math.PI) / 180;
        const endAngleRad = ((currentAngle + sliceAngle) * Math.PI) / 180;

        const x1 = centerX + radius * Math.cos(startAngleRad);
        const y1 = centerY + radius * Math.sin(startAngleRad);
        const x2 = centerX + radius * Math.cos(endAngleRad);
        const y2 = centerY + radius * Math.sin(endAngleRad);

        const largeArc = sliceAngle > 180 ? 1 : 0;

        path = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;
      }

      currentAngle += sliceAngle;

      return {
        name: c.name,
        votes,
        percent,
        color: colors[i % colors.length],
        full_circle,
        path
      };
    });
  }
}