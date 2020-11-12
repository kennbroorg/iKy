import { ChangeDetectionStrategy, Component, OnInit, TemplateRef } from '@angular/core';
// import { NbThemeService } from '@nebular/theme';

// Gatherer Service
import { DataGatherInfoService } from '../../@core/data/data-gather-info.service';
import { LocalDataSource } from 'ng2-smart-table';
import { NbDialogService } from '@nebular/theme';

@Component({
    selector: 'ngx-apikeys',
    templateUrl: './apikeys.component.html',
    styles: [`
        nb-card {
            transform: translate3d(0, 0, 0);
        }
    `],
    changeDetection: ChangeDetectionStrategy.Default,
})

export class ApiKeysComponent implements OnInit {
    public  keys: any;

    settings = {
      add: {
        addButtonContent: '<i class="nb-plus"></i>',
        createButtonContent: '<i class="nb-checkmark"></i>',
        cancelButtonContent: '<i class="nb-close"></i>',
      },
      edit: {
        editButtonContent: '<i class="nb-edit"></i>',
        saveButtonContent: '<i class="nb-checkmark"></i>',
        cancelButtonContent: '<i class="nb-close"></i>',
      },
      delete: {
        deleteButtonContent: '<i class="nb-trash"></i>',
        confirmDelete: true,
      },
      columns: {
        id: {
          title: 'ID',
          type: 'number',
        },
        name: {
          title: 'Key name',
          type: 'string',
        },
        key: {
          title: 'Key value',
          type: 'string',
        },
      },
    };

    source: LocalDataSource = new LocalDataSource();

    constructor(private dialogService: NbDialogService,
                private executeHttp: DataGatherInfoService) {
    }

    ngOnInit() {
        console.log('ApiKeysComponent ngOnInit');

        // Get Api Keys
        this.executeHttp.getApiKeys$('')
            .subscribe(data => this.source.load(data.keys),
                       err => console.error('Ops: ', err.message),
            );
        console.log('Source: ', this.source);
    }

    onDeleteConfirm(event): void {
        if (window.confirm('Are you sure you want to delete?')) {
            event.confirm.resolve();
        } else {
            event.confirm.reject();
        }
    }

    openDialog(dialog: TemplateRef<any>) {
      this.dialogService.open(dialog);
    }

    updateConfirm() {
        this.source.getAll()
            .then(function (data) {
                    // Get Api Keys
                    this.executeHttp.getApiKeys$(data)
                        .subscribe(datain => this.source.load(datain.keys),
                                   err => console.error('Ops: ', err.message),
                        );
                  }.bind(this),
                  err => console.error('Ops: ', err.message),
            );
    }

    generateDownloadJsonUri() {
        const Json = this.source.getAll();
        console.log(Json);
        const sJson = JSON.stringify(Json['__zone_symbol__value']);
        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/json;charset=UTF-8,' + encodeURIComponent(sJson));
        element.setAttribute('download', 'apikeys.json');
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click(); // simulate click
        document.body.removeChild(element);
    }

}
