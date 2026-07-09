import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-vote-recorded',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './already-voted.html',
  styleUrls: ['./already-voted.css']
})
export class VoteRecordedComponent implements OnInit {

  // Array to hold any success messages passed via state or service
  messages: string[] = [];

  constructor(private api: ApiService, private router: Router) { }

  ngOnInit(): void {
    // Example: You might read from a state management service here
    // this.messages = ['Your vote was securely encrypted and submitted.'];
  }

  logout(): void {
    this.api.logout().subscribe({
      next: () => {
        sessionStorage.clear();
        this.router.navigate(['/']);
      },
      error: () => {
        sessionStorage.clear();
        this.router.navigate(['/']);
      }
    });
  }

}