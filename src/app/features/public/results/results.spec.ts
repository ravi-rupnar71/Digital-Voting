import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { throwError } from 'rxjs';

import { ApiService } from '../../../core/services/api';
import { ResultsComponent } from './results';

describe('ResultsComponent', () => {
  let component: ResultsComponent;
  let fixture: ComponentFixture<ResultsComponent>;
  let apiService: jasmine.SpyObj<ApiService>;

  beforeEach(async () => {
    apiService = jasmine.createSpyObj('ApiService', ['getResults']);

    await TestBed.configureTestingModule({
      imports: [ResultsComponent, RouterTestingModule],
      providers: [{ provide: ApiService, useValue: apiService }],
    }).compileComponents();

    fixture = TestBed.createComponent(ResultsComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should fall back to the backend results URL when the API call fails', async () => {
    apiService.getResults.and.returnValue(throwError(() => new Error('boom')));

    const fetchSpy = spyOn(window, 'fetch').and.returnValue(Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ candidates: [{ name: 'Ada', party: 'Test', votes: 1 }], total_votes: 1 })
    } as Response));

    component.loadAndDisplayResults();
    await fixture.whenStable();

    expect(fetchSpy).toHaveBeenCalledWith(
      'http://localhost:5000/api/results',
      jasmine.objectContaining({ credentials: 'include' })
    );
    expect(component.candidates.length).toBe(1);
    expect(component.total).toBe(1);
  });
});
