import { Component, Input, OnInit, OnChanges } from '@angular/core';
// import { ColumnMode  } from '@swimlane/ngx-datatable/lib/types/column-mode.type';


@Component({
  selector: 'ngx-taskexec',
  templateUrl: './taskexec.component.html',
  styleUrls: ['./taskexec.component.scss'],
})
export class TaskexecComponent {
  @Input() private dataTask: any;
  @Input() private TaskPP: number;
  @Input() private TaskPS: number;
  public rows: any;

  // ColumnMode = ColumnMode;

  constructor() {}

  ngOnInit() {
      this.rows = this.dataTask;
      // this.updateTasks();
  }

  ngOnChanges(){
    // this.updateTasks();
    this.rows = this.dataTask;
    this.rows = [...this.rows];
  }

  /* Conditional Classes */
  getStateColor({ row, column, value }): any {
    console.warn(value);
    return {
      'success-color': value === 'SUCCESS', 
      'process-color': value === 'PROCESS',
      'pending-color': value === 'PENDING',
      'failure-color': value === 'FAILURE'
    };
  }

}
