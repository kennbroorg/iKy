import { Component, Input, OnInit, OnChanges } from '@angular/core';
import { NbSortDirection, NbSortRequest, NbTreeGridDataSource, NbTreeGridDataSourceBuilder } from '@nebular/theme';

interface TreeNode<T> {
  data: T;
  children?: TreeNode<T>[];
  expanded?: boolean;
}

interface FSEntry {
  module: string;
  param: string;
  from: string;
  score: any;
  stateIcon: string;
}

@Component({
  selector: 'ngx-taskexec',
  templateUrl: './taskexec.component.html',
  styleUrls: ['./taskexec.component.scss'],
})
export class TaskexecComponent {
  @Input() private dataTask: any;
  @Input() private TaskPP: number;
  @Input() private TaskPS: number;
  customColumn = 'module';
  defaultColumns = [ 'param', 'from' ];
  scoreColumn = 'score';
  stateColumn = 'stateIcon';
  allColumns = [ this.customColumn, ...this.defaultColumns, this.scoreColumn, this.stateColumn ];

  dataSource: NbTreeGridDataSource<FSEntry>;
  changelog: string[] = [];

  sortColumn: string;
  sortDirection: NbSortDirection = NbSortDirection.NONE;

  private data: TreeNode<FSEntry>[] = [

    {
      data: { module: 'Tasklist', param: 'Param', from: 'From', score: 'Score', stateIcon: 'State' },
      children: [
      ],
    },
  ];

  constructor(private dataSourceBuilder: NbTreeGridDataSourceBuilder<FSEntry>) {
    this.dataSource = this.dataSourceBuilder.create(this.data);
  }

  ngOnInit() {
      this.updateTasks();
  }

  ngOnChanges(){
    this.updateTasks();
  }

  updateTasks() {
      // console.log("taskexec data", this.data);
      // console.log("taskexec dataTask", this.dataTask);

    this.data = [
      {
        data: { module: 'Tasklist', param: 'Param', from: 'From', score: 'Score', stateIcon: 'State' },
        children: [
        ],
      },
    ];

    for (let i in this.dataTask) {
        // console.log("taskexec", i, this.dataTask[i]);
        // parse_obj['theTeam'].push({"teamId":"4","status":"pending"});
        this.data[0]['children'].push(
            { data: {
                module: this.dataTask[i].module,
                param: this.dataTask[i].param,
                from: this.dataTask[i].from,
                score: this.dataTask[i].score,
                stateIcon: this.dataTask[i].state,
                }
            }
        );
        
    }
      console.log("taskexec JSON", this.data)
  }

  updateSort(sortRequest: NbSortRequest): void {
    this.sortColumn = sortRequest.column;
    this.sortDirection = sortRequest.direction;
  }

  getSortDirection(column: string): NbSortDirection {
    if (this.sortColumn === column) {
      return this.sortDirection;
    }
    return NbSortDirection.NONE;
  }

  getShowOn(index: number) {
    const minWithForMultipleColumns = 400;
    const nextColumnStep = 100;
    return minWithForMultipleColumns + (nextColumnStep * index);
  }
}

@Component({
  selector: 'ngx-fs-icon',
  template: `
    <nb-tree-grid-row-toggle [expanded]="expanded" *ngIf="isDir(); else fileIcon">
    </nb-tree-grid-row-toggle>
    <ng-template #fileIcon>
      <!-- <nb-icon icon="file-text-outline"></nb-icon> -->
      <i class="fas fa-cog"></i>
    </ng-template>
  `,
})
export class FsIconComponent {
  @Input() kind: string;
  @Input() expanded: boolean;

  isDir(): boolean {
    return this.kind === 'Tasklist';
  }
}
