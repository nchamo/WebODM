import '../css/ImportTaskPanel.scss';
import React from 'react';
import PropTypes from 'prop-types';
import ErrorMessage from './ErrorMessage';
import Select from 'react-select';
import NewTaskPanel from './NewTaskPanel';

class ImportImagesFromPiwigoPanel extends React.Component {
  static defaultProps = {
  };

  static propTypes = {
      onImported: PropTypes.func.isRequired,
      onCancel: PropTypes.func,
      projectId: PropTypes.number.isRequired
  };

  constructor(props){
    super(props);

    this.state = {
      error: "",
      options: [],
      loadingOptionsFromPiwigo: false,
      confirmedAlbumSelection: false,
      importAlbum: null
    };
    
    this.loadPiwigoAlbums();
  }

  cancel = (e) => {
    this.props.onCancel();
  }
  
  handleChangeImportAlbum = (e) => {
    this.setState({importAlbum: e});
  }

  handleConfirmImportAlbum = () => {
    this.setState({confirmedAlbumSelection: true});
  }

  loadPiwigoAlbums = () => {
    this.setState({loadingOptionsFromPiwigo: true});
    $.get(`/api/albums`)
    .done(json => {
      json.forEach(album => {
        album.label = `${album.name} (${album.images} images)`;
        album.value = album.album_id;
      })
      this.setState({options: json});
    })
    .fail((error) => {
        this.setState({loadingOptionsFromPiwigo: false, error: "Cannot load albums from Piwigo. Check your internet connection."});
    });
  }
  
  handleTaskSaved = (taskInfo) => {
    $.post(`/api/projects/${this.props.projectId}/tasks/importimages`,
      {
        album_id: this.state.importAlbum.album_id,
        name: taskInfo.name,
        processing_node: taskInfo.selectedNode.id,
        options: JSON.stringify(taskInfo.options)
      }
    ).done(json => {
      this.setState({confirmedAlbumSelection: false});
    
      if (json.id){
        this.props.onImported();
      }else{
        this.setState({error: json.error || `Cannot import from Piwigo, server responded: ${JSON.stringify(json)}`});
      }
    })
    .fail(() => {
        this.setState({confirmedAlbumSelection: false, error: "Cannot import from Piwigo. Check your internet connection."});
    });
  }
  
  render() {
    return (
      <div className="theme-background-highlight">
        <div className="form-horizontal">
          <div className="import-task-panel">
            <ErrorMessage bind={[this, 'error']} />

            <button type="button" className="close theme-color-primary" aria-label="Close" onClick={this.cancel}><span aria-hidden="true">&times;</span></button>
            <h4>Import Images From Piwigo</h4>
            { this.state.confirmedAlbumSelection === false ?
              <div className="form-inline">
                <p>You can import the images in a Piwigo album to use for a new task.</p>     
                <div className="form-group">
                  <div style={{width:600, display: 'inline-block'}}>
                    <Select
                      className="basic-single"
                      classNamePrefix="select"
                      isLoading={this.state.loadingOptionsFromPiwigo}
                      isClearable={false}
                      isSearchable={true}
                      onChange={this.handleChangeImportAlbum}
                      options={this.state.options}
                      placeholder={this.state.loadingOptionsFromPiwigo ? "Fetching Piwigo albums..." : "Please select a Piwigo album"}
                      name="options"
                    />
                  </div>
                  <button onClick={this.handleConfirmImportAlbum}
                          disabled={!this.state.importAlbum} 
                          className="btn-import btn btn-primary"><i className="glyphicon glyphicon-cloud-download"></i> Import</button>
                </div>
                <p><b>Note</b>: when importing an album, you only import the images inside. All the sub-albums are ignored. Also, there is a limit of 500 images uploaded per album.</p>
              </div>
            : "" }
          </div>
          {this.state.confirmedAlbumSelection ? 
            <NewTaskPanel
              initialName={this.state.importAlbum.name}
              onSave={this.handleTaskSaved}
              onCancel={this.cancel}
              filesCount={this.state.importAlbum.images}
              showResize={false}
              getFiles={() => [] }
            /> : "" }
        </div>
      </div>
    );
  }
}

export default ImportImagesFromPiwigoPanel;
