import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { ApiService } from '../../../core/services/api';
import { EditCandidateComponent } from './edit-candidate';

describe('EditCandidateComponent', () => {
  let component: EditCandidateComponent;
  let fixture: ComponentFixture<EditCandidateComponent>;
  let apiService: jasmine.SpyObj<ApiService>;

  beforeEach(async () => {
    apiService = jasmine.createSpyObj('ApiService', ['getCandidate']);
    apiService.getCandidate.and.returnValue(of({
      name: 'Real Candidate',
      party: 'Real Party',
      email: 'real-candidate@example.com'
    }));

    await TestBed.configureTestingModule({
      imports: [EditCandidateComponent, RouterTestingModule],
      providers: [
        { provide: ApiService, useValue: apiService },
        { provide: ActivatedRoute, useValue: { paramMap: of({ get: () => '8' }) } }
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(EditCandidateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load the real candidate email from the API', () => {
    expect(apiService.getCandidate).toHaveBeenCalledWith(8);
    expect(component.editForm.get('email')?.value).toBe('real-candidate@example.com');
  });
});
